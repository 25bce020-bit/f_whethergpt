import asyncio
from datetime import date, datetime, timedelta, timezone
import unittest

from app.services.agromet_service import (
    get_agromet_advisory,
    normalize_agromet_payload,
    normalize_crop_name,
    resolve_agromet_location,
)
from app.services.farmer_service import (
    build_farmer_advisory,
    format_farmer_advisory,
)


class AgrometServiceTests(unittest.TestCase):
    def test_normalize_crop_name(self):
        self.assertEqual(normalize_crop_name("Wheat"), "wheat")
        self.assertEqual(normalize_crop_name("Paddy"), "rice")
        self.assertEqual(normalize_crop_name("rice"), "rice")
        self.assertEqual(normalize_crop_name(" Cotton "), "cotton")
        self.assertIsNone(normalize_crop_name(None))
        self.assertIsNone(normalize_crop_name(""))

    def test_resolve_agromet_location_india(self):
        # Ahmedabad, Gujarat
        ahmedabad = resolve_agromet_location(
            latitude=23.0225,
            longitude=72.5714,
            location_name="Ahmedabad",
            state_name="Gujarat",
            country_code="IN",
        )
        self.assertTrue(ahmedabad["supported"])
        self.assertEqual(ahmedabad["state_id"], 24)
        self.assertEqual(ahmedabad["state_name"], "Gujarat")

        # Nagpur, Maharashtra
        nagpur = resolve_agromet_location(
            latitude=21.1458,
            longitude=79.0882,
            location_name="Nagpur",
            state_name="Maharashtra",
            country_code="IN",
        )
        self.assertTrue(nagpur["supported"])
        self.assertEqual(nagpur["state_id"], 20)

    def test_resolve_agromet_location_international_or_out_of_bounds(self):
        london = resolve_agromet_location(
            latitude=51.5074,
            longitude=-0.1278,
            location_name="London",
            state_name="Greater London",
            country_code="GB",
        )
        self.assertFalse(london["supported"])
        self.assertIn("India only", london["reason"])

        tokyo = resolve_agromet_location(
            latitude=35.6762,
            longitude=139.6503,
            location_name="Tokyo",
            state_name="Tokyo",
            country_code="JP",
        )
        self.assertFalse(tokyo["supported"])

    def test_normalize_agromet_payload_empty(self):
        loc_meta = {
            "state_name": "Gujarat",
            "district_name": "Ahmedabad",
            "latitude": 23.0225,
            "longitude": 72.5714,
        }
        res = normalize_agromet_payload(None, location_meta=loc_meta)
        self.assertFalse(res["available"])
        self.assertEqual(res["status"], "empty")
        self.assertEqual(res["source"], "IMD Agromet/GKMS")
        self.assertEqual(res["advisories"], [])
        self.assertIn("not found", res["note"])
        self.assertIn("source_attribution", res)

    def test_normalize_agromet_payload_valid_advisories(self):
        loc_meta = {
            "state_name": "Gujarat",
            "district_name": "Ahmedabad",
            "latitude": 23.0225,
            "longitude": 72.5714,
        }
        tomorrow_iso = (date.today() + timedelta(days=5)).isoformat()
        sample_imd_response = {
            "IsSuccessful": True,
            "ObjCropAdvisoryDetailsList": [
                {
                    "CropAdvisoryID": 101,
                    "CropName": "Wheat",
                    "VarietyName": "GW-496",
                    "Title": "Wheat Crown Root Initiation Advisory",
                    "State": "Gujarat",
                    "District": "Ahmedabad",
                    "Block": "Daskroi",
                    "WeatherCondition": "Mainly clear sky and dry weather forecast.",
                    "WeatherConditionRegional": "મુખ્યત્વે સ્વચ્છ આકાશ અને સૂકું હવામાન.",
                    "Recommendations": "Apply first irrigation at CRI stage (20-25 days after sowing).",
                    "RecommendationsRegional": "વાવણી પછી ૨૦-૨૫ દિવસે સીઆરઆઈ તબક્કે પ્રથમ પિયત આપવું.",
                    "RegionalLanguage": "Gujarati",
                    "PeriodStartDate": date.today().isoformat(),
                    "PeriodEndDate": tomorrow_iso,
                },
                {
                    "CropAdvisoryID": 102,
                    "CropName": "Cotton",
                    "Title": "Cotton Boll Formation Advisory",
                    "Recommendations": "Pick mature cotton bolls during sunny hours.",
                    "PeriodEndDate": tomorrow_iso,
                },
            ],
        }

        # 1. User asks for Wheat
        wheat_res = normalize_agromet_payload(
            sample_imd_response,
            location_meta=loc_meta,
            crop_filter="wheat",
        )
        self.assertTrue(wheat_res["available"])
        self.assertEqual(len(wheat_res["advisories"]), 1)
        adv = wheat_res["advisories"][0]
        self.assertEqual(adv["crop"], "Wheat")
        self.assertEqual(adv["variety"], "GW-496")
        self.assertIn("Apply first irrigation", adv["recommendation"])
        self.assertIn("પ્રથમ પિયત", adv["recommendation_regional"])
        self.assertEqual(adv["language"], "Gujarati")
        self.assertEqual(adv["valid_until"], tomorrow_iso)

        # 2. User asks for Cotton
        cotton_res = normalize_agromet_payload(
            sample_imd_response,
            location_meta=loc_meta,
            crop_filter="cotton",
        )
        self.assertTrue(cotton_res["available"])
        self.assertEqual(len(cotton_res["advisories"]), 1)
        self.assertEqual(cotton_res["advisories"][0]["crop"], "Cotton")

        # 3. User asks for unrelated crop (e.g. Maize)
        maize_res = normalize_agromet_payload(
            sample_imd_response,
            location_meta=loc_meta,
            crop_filter="maize",
        )
        self.assertFalse(maize_res["available"])
        self.assertEqual(len(maize_res["advisories"]), 0)

    def test_normalize_agromet_payload_filters_expired_advisory(self):
        loc_meta = {"state_name": "Gujarat", "district_name": "Ahmedabad"}
        yesterday_iso = (date.today() - timedelta(days=2)).isoformat()
        expired_response = {
            "ObjCropAdvisoryDetailsList": [
                {
                    "CropAdvisoryID": 999,
                    "CropName": "Wheat",
                    "Recommendations": "Old expired recommendation.",
                    "PeriodEndDate": yesterday_iso,
                }
            ]
        }
        res = normalize_agromet_payload(expired_response, location_meta=loc_meta, crop_filter="wheat")
        self.assertFalse(res["available"])
        self.assertEqual(len(res["advisories"]), 0)

    def test_build_and_format_farmer_advisory_integration(self):
        agromet_payload = {
            "available": True,
            "status": "available",
            "source": "IMD Agromet/GKMS",
            "location": {"state": "Gujarat", "district": "Ahmedabad"},
            "advisories": [
                {
                    "id": 101,
                    "title": "Wheat Irrigation Advisory",
                    "crop": "Wheat",
                    "recommendation": "Provide light irrigation prior to expected temperature rise.",
                    "valid_until": (date.today() + timedelta(days=3)).isoformat(),
                }
            ],
            "source_attribution": {
                "provider": "IMD Agromet / GKMS",
                "url": "https://agromet.imd.gov.in",
            },
        }

        advisory = build_farmer_advisory(
            crop="wheat",
            growth_stage="vegetative",
            current_weather={"temperature_c": 28.0, "precipitation_mm": 0, "wind_speed_kmh": 10},
            forecast=[{"date": date.today().isoformat(), "temperature_max_c": 32, "precipitation_mm": 0}],
            hourly_forecast=[],
            imd_warnings=[],
            agromet_advisory=agromet_payload,
        )

        self.assertEqual(advisory["agromet_status"], "available")
        self.assertIsNotNone(advisory["agromet_advisory"])
        self.assertEqual(len(advisory["agromet_advisory"]["advisories"]), 1)

        formatted = format_farmer_advisory(advisory)
        self.assertIn("Official IMD Agromet / GKMS Advisory", formatted)
        self.assertIn("Wheat Irrigation Advisory", formatted)
        self.assertIn("Provide light irrigation", formatted)

    def test_get_agromet_advisory_resilience(self):
        # International location should return structured unavailable object without network calls
        loop = asyncio.new_event_loop()
        try:
            asyncio.set_event_loop(loop)
            res = loop.run_until_complete(
                get_agromet_advisory(
                    latitude=51.5074,
                    longitude=-0.1278,
                    location_name="London",
                    country_code="GB",
                )
            )
            self.assertFalse(res["available"])
            self.assertEqual(res["status"], "unsupported_location")
            self.assertIn("India only", res["note"])
        finally:
            loop.close()


if __name__ == "__main__":
    unittest.main()
