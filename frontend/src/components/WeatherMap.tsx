import { useEffect } from 'react';
import { MapContainer, Marker, TileLayer, useMap, useMapEvents } from 'react-leaflet';
import L from 'leaflet';
import type { MapWarning } from '../api/types';

const selectedIcon = L.divIcon({ className: 'weather-map-marker', html: '<span aria-hidden="true">●</span>', iconSize: [24, 24], iconAnchor: [12, 12] });
const warningIcon = L.divIcon({ className: 'weather-warning-marker', html: '<span aria-hidden="true">!</span>', iconSize: [20, 20], iconAnchor: [10, 10] });

function ClickHandler({onSelect}:{onSelect:(latitude:number,longitude:number)=>void}) { useMapEvents({click(event){onSelect(event.latlng.lat,event.latlng.lng)}}); return null; }
function CenterMap({latitude,longitude}:{latitude?:number;longitude?:number}) { const map=useMap(); useEffect(()=>{if(latitude!==undefined&&longitude!==undefined) map.setView([latitude,longitude],10)},[latitude,longitude,map]); return null; }

export function WeatherMap({latitude,longitude,warnings,onSelect}:{latitude?:number;longitude?:number;warnings:MapWarning[];onSelect:(latitude:number,longitude:number)=>void}) { const center:[number,number]=latitude!==undefined&&longitude!==undefined?[latitude,longitude]:[20.5937,78.9629]; return <MapContainer className="weather-map" center={center} zoom={latitude===undefined?5:10} scrollWheelZoom aria-label="Interactive weather map"><TileLayer attribution='© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors' url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"/><CenterMap latitude={latitude} longitude={longitude}/><ClickHandler onSelect={onSelect}/>{latitude!==undefined&&longitude!==undefined&&<Marker position={[latitude,longitude]} icon={selectedIcon}/>} {warnings.filter(warning=>warning.location).map(warning=><Marker key={warning.id??`${warning.location?.latitude}-${warning.location?.longitude}`} position={[warning.location!.latitude,warning.location!.longitude]} icon={warningIcon}/>)}</MapContainer> }
