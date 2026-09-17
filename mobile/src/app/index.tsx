import { WebView } from 'react-native-webview';
import { SafeAreaView, StyleSheet } from 'react-native';

const WEBSITE_URL = 'http://10.158.54.251:5173'; // your frontend's IP:port

export default function Index() {
  return (
    <SafeAreaView style={styles.container}>
      <WebView
        source={{ uri: WEBSITE_URL }}
        style={{ flex: 1 }}
        startInLoadingState
        javaScriptEnabled
        domStorageEnabled
        originWhitelist={['*']}
      />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
});