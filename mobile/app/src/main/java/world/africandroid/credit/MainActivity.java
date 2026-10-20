package world.africandroid.credit;
import android.app.Activity;import android.os.Bundle;import android.webkit.*;import android.net.Uri;import android.content.Intent;
public class MainActivity extends Activity {
 private WebView web;
 @Override public void onCreate(Bundle saved){super.onCreate(saved);web=new WebView(this);setContentView(web);web.getSettings().setJavaScriptEnabled(true);web.getSettings().setDomStorageEnabled(true);web.getSettings().setAllowFileAccess(false);web.getSettings().setAllowContentAccess(false);web.getSettings().setMixedContentMode(WebSettings.MIXED_CONTENT_NEVER_ALLOW);WebView.setWebContentsDebuggingEnabled(false);web.setWebViewClient(new WebViewClient(){@Override public boolean shouldOverrideUrlLoading(WebView view,WebResourceRequest request){Uri u=request.getUrl();if("https".equals(u.getScheme())&&Uri.parse(BuildConfig.APP_URL).getHost().equals(u.getHost()))return false;if("https".equals(u.getScheme())){startActivity(new Intent(Intent.ACTION_VIEW,u));}return true;}});web.loadUrl(BuildConfig.APP_URL);}
 @Override public void onBackPressed(){if(web.canGoBack())web.goBack();else super.onBackPressed();}
}
