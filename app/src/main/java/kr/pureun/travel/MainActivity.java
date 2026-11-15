package kr.pureun.travel;

import android.Manifest;
import android.app.Activity;
import android.content.ClipData;
import android.content.ContentValues;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.provider.MediaStore;
import android.util.Log;
import android.util.SparseArray;
import android.view.WindowManager;
import android.webkit.ConsoleMessage;
import android.webkit.PermissionRequest;
import android.webkit.ValueCallback;
import android.webkit.WebChromeClient;
import android.webkit.WebResourceRequest;
import android.webkit.WebResourceResponse;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;

import java.io.ByteArrayInputStream;
import java.io.InputStream;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.Map;

/** 화면은 assets/index.html(웹 통역 앱)을 그대로 쓰고, 마이크·목소리·폰 AI 번역·파일은 Bridge로 연결한다. */
public class MainActivity extends Activity {
    static final String TAG = "TravelApp";
    static final String HOST = "app.travel.local";
    static final int REQ_FILE = 11;

    final Handler ui = new Handler(Looper.getMainLooper());
    WebView web;
    Bridge bridge;
    SttEngine stt;
    TtsEngine tts;
    LlmEngine llm;
    ModelStore models;
    LocalStt lstt;
    volatile boolean bgKeep;   // 화면이 꺼져도 계속 듣기
    volatile boolean playKeep; // 화면이 꺼져도 끝까지 읽기

    private ValueCallback<Uri[]> fileCb;
    private Uri cameraUri;
    private final SparseArray<Runnable[]> permCbs = new SparseArray<>();
    private int permSeq = 100;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        getWindow().setStatusBarColor(0xff000000);
        setVolumeControlStream(android.media.AudioManager.STREAM_MUSIC);

        models = new ModelStore(this);
        llm = new LlmEngine(this);
        stt = new SttEngine(this);
        lstt = new LocalStt(this);
        tts = new TtsEngine(this);
        bridge = new Bridge(this);

        WebView.setWebContentsDebuggingEnabled(true);
        web = new WebView(this);
        web.setBackgroundColor(0xffffffff);
        setContentView(web);

        WebSettings s = web.getSettings();
        s.setJavaScriptEnabled(true);
        s.setDomStorageEnabled(true);
        s.setDatabaseEnabled(true);
        s.setMediaPlaybackRequiresUserGesture(false);
        s.setAllowFileAccess(false);
        s.setSupportZoom(false);
        s.setTextZoom(100);
        s.setMixedContentMode(WebSettings.MIXED_CONTENT_COMPATIBILITY_MODE);

        web.addJavascriptInterface(bridge, "AndroidBridge");
        web.setWebViewClient(new Client());
        web.setWebChromeClient(new Chrome());
        web.setOverScrollMode(WebView.OVER_SCROLL_NEVER);
        web.loadUrl("https://" + HOST + "/index.html");

        // 마이크 권한은 처음 켤 때 미리 물어봄 (통역 버튼을 눌렀을 때 바로 듣도록)
        Runnable nothing = new Runnable() { @Override public void run() { } };
        if (Build.VERSION.SDK_INT >= 33) ensurePerms(new String[]{Manifest.permission.RECORD_AUDIO, Manifest.permission.POST_NOTIFICATIONS}, nothing, nothing);
        else if (!has(Manifest.permission.RECORD_AUDIO)) ensurePerms(new String[]{Manifest.permission.RECORD_AUDIO}, nothing, nothing);
    }

    /** JS 쪽 window.__nat.<fn>(json) 호출 */
    void emit(final String fn, final String json) {
        ui.post(new Runnable() {
            @Override public void run() {
                if (web != null) web.evaluateJavascript("window.__nat&&window.__nat." + fn + "(" + json + ")", null);
            }
        });
    }

    private final java.util.HashSet<String> awake = new java.util.HashSet<>();

    /** 화면 꺼짐 방지 (마이크 사용 중·모델 받는 중). 누가 켰는지 따로 기억해 둔다 */
    void keepAwake(final String who, final boolean on) {
        ui.post(new Runnable() {
            @Override public void run() {
                if (on) awake.add(who); else awake.remove(who);
                if (!awake.isEmpty()) getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);
                else getWindow().clearFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);
            }
        });
    }

    // ── 권한 ──
    boolean has(String perm) {
        return checkSelfPermission(perm) == PackageManager.PERMISSION_GRANTED;
    }

    /** 권한이 있으면 ok, 없으면 물어본 뒤 ok/deny (UI 스레드에서 호출) */
    void ensurePerms(String[] perms, Runnable ok, Runnable deny) {
        ArrayList<String> need = new ArrayList<>();
        for (String p : perms) if (!has(p)) need.add(p);
        if (need.isEmpty()) { ok.run(); return; }
        int code = permSeq++;
        permCbs.put(code, new Runnable[]{ok, deny});
        requestPermissions(need.toArray(new String[0]), code);
    }

    @Override
    public void onRequestPermissionsResult(int code, String[] perms, int[] results) {
        Runnable[] cb = permCbs.get(code);
        if (cb == null) return;
        permCbs.remove(code);
        boolean all = results.length > 0;
        for (int r : results) if (r != PackageManager.PERMISSION_GRANTED) all = false;
        Runnable r = all ? cb[0] : cb[1];
        if (r != null) r.run();
    }

    // ── 화면(웹) 파일을 앱 안에서 꺼내 줌: https://app.travel.local/… → assets ──
    class Client extends WebViewClient {
        @Override
        public WebResourceResponse shouldInterceptRequest(WebView view, WebResourceRequest req) {
            Uri u = req.getUrl();
            if (!HOST.equals(u.getHost())) return null;
            String path = u.getPath();
            if (path == null || path.equals("/") || path.isEmpty()) path = "/index.html";
            String name = path.substring(1);
            Map<String, String> headers = new HashMap<>();
            headers.put("Cache-Control", "no-cache");
            if (name.startsWith("rec/")) {                 // 저장한 소리 듣기: /rec/<파일>?a=<시작 표본>&b=<끝 표본>
                long a = 0, b = 0;
                try { a = Long.parseLong(u.getQueryParameter("a")); } catch (Exception ignored) { }
                try { b = Long.parseLong(u.getQueryParameter("b")); } catch (Exception ignored) { }
                byte[] wav = lstt == null ? null : lstt.recWav(MainActivity.this, name.substring(4), a, b);
                if (wav == null) return new WebResourceResponse("text/plain", "utf-8", 404, "Not Found", headers, new ByteArrayInputStream(new byte[0]));
                headers.put("Content-Length", String.valueOf(wav.length));
                return new WebResourceResponse("audio/wav", null, 200, "OK", headers, new ByteArrayInputStream(wav));
            }
            try {
                InputStream in = getAssets().open(name);
                return new WebResourceResponse(mimeOf(name), "utf-8", 200, "OK", headers, in);
            } catch (Exception e) {
                return new WebResourceResponse("text/plain", "utf-8", 404, "Not Found", headers,
                        new ByteArrayInputStream(new byte[0]));
            }
        }

        @Override
        public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest req) {
            Uri u = req.getUrl();
            if (HOST.equals(u.getHost())) return false;
            try { startActivity(new Intent(Intent.ACTION_VIEW, u)); } catch (Exception ignored) { }
            return true;
        }
    }

    static String mimeOf(String n) {
        n = n.toLowerCase();
        if (n.endsWith(".html")) return "text/html";
        if (n.endsWith(".js")) return "application/javascript";
        if (n.endsWith(".css")) return "text/css";
        if (n.endsWith(".png")) return "image/png";
        if (n.endsWith(".svg")) return "image/svg+xml";
        if (n.endsWith(".json") || n.endsWith(".webmanifest")) return "application/json";
        return "application/octet-stream";
    }

    class Chrome extends WebChromeClient {
        @Override
        public void onPermissionRequest(final PermissionRequest request) {
            ArrayList<String> need = new ArrayList<>();
            for (String r : request.getResources()) {
                if (PermissionRequest.RESOURCE_AUDIO_CAPTURE.equals(r)) need.add(Manifest.permission.RECORD_AUDIO);
                if (PermissionRequest.RESOURCE_VIDEO_CAPTURE.equals(r)) need.add(Manifest.permission.CAMERA);
            }
            if (need.isEmpty()) { request.deny(); return; }
            ensurePerms(need.toArray(new String[0]), new Runnable() {
                @Override public void run() { request.grant(request.getResources()); }
            }, new Runnable() {
                @Override public void run() { request.deny(); }
            });
        }

        @Override
        public boolean onShowFileChooser(WebView w, ValueCallback<Uri[]> cb, FileChooserParams params) {
            if (fileCb != null) fileCb.onReceiveValue(null);
            fileCb = cb;
            final String[] accept = params.getAcceptTypes();
            final boolean multiple = params.getMode() == FileChooserParams.MODE_OPEN_MULTIPLE;
            boolean image = false;
            for (String a : accept) if (a != null && a.startsWith("image/")) image = true;
            if (params.isCaptureEnabled() && image && Build.VERSION.SDK_INT >= 29) {
                ensurePerms(new String[]{Manifest.permission.CAMERA}, new Runnable() {
                    @Override public void run() { openCamera(); }
                }, new Runnable() {
                    @Override public void run() { openPicker(accept, multiple); }
                });
            } else openPicker(accept, multiple);
            return true;
        }

        @Override
        public boolean onConsoleMessage(ConsoleMessage m) {
            Log.d(TAG, "js: " + m.message() + " @" + m.lineNumber());
            return true;
        }
    }

    private void openCamera() {
        try {
            ContentValues v = new ContentValues();
            v.put(MediaStore.Images.Media.DISPLAY_NAME, "travel-" + System.currentTimeMillis() + ".jpg");
            v.put(MediaStore.Images.Media.MIME_TYPE, "image/jpeg");
            cameraUri = getContentResolver().insert(MediaStore.Images.Media.EXTERNAL_CONTENT_URI, v);
            Intent i = new Intent(MediaStore.ACTION_IMAGE_CAPTURE);
            i.putExtra(MediaStore.EXTRA_OUTPUT, cameraUri);
            i.addFlags(Intent.FLAG_GRANT_WRITE_URI_PERMISSION | Intent.FLAG_GRANT_READ_URI_PERMISSION);
            startActivityForResult(i, REQ_FILE);
        } catch (Exception e) {
            Log.w(TAG, "camera", e);
            dropCameraUri();
            openPicker(new String[]{"image/*"}, false);
        }
    }

    private void openPicker(String[] accept, boolean multiple) {
        try {
            ArrayList<String> mimes = new ArrayList<>();
            boolean any = false;
            for (String a : accept) {
                if (a == null) continue;
                for (String t : a.split(",")) {
                    t = t.trim();
                    if (t.isEmpty()) continue;
                    if (t.contains("/")) mimes.add(t); else any = true; // ".txt" 같은 확장자는 모든 파일로
                }
            }
            Intent i = new Intent(Intent.ACTION_GET_CONTENT);
            i.addCategory(Intent.CATEGORY_OPENABLE);
            if (any || mimes.isEmpty()) i.setType("*/*");
            else if (mimes.size() == 1) i.setType(mimes.get(0));
            else { i.setType("*/*"); i.putExtra(Intent.EXTRA_MIME_TYPES, mimes.toArray(new String[0])); }
            if (multiple) i.putExtra(Intent.EXTRA_ALLOW_MULTIPLE, true);
            startActivityForResult(Intent.createChooser(i, "파일 고르기"), REQ_FILE);
        } catch (Exception e) {
            Log.w(TAG, "picker", e);
            if (fileCb != null) { fileCb.onReceiveValue(null); fileCb = null; }
        }
    }

    private void dropCameraUri() {
        if (cameraUri != null) {
            try { getContentResolver().delete(cameraUri, null, null); } catch (Exception ignored) { }
            cameraUri = null;
        }
    }

    @Override
    protected void onActivityResult(int req, int result, Intent data) {
        if (req != REQ_FILE) { super.onActivityResult(req, result, data); return; }
        ValueCallback<Uri[]> cb = fileCb;
        fileCb = null;
        if (cb == null) { dropCameraUri(); return; }
        Uri[] out = null;
        if (result == RESULT_OK) {
            if (cameraUri != null && (data == null || (data.getData() == null && data.getClipData() == null))) {
                out = new Uri[]{cameraUri};
                cameraUri = null;
            } else if (data != null) {
                ClipData clip = data.getClipData();
                if (clip != null && clip.getItemCount() > 0) {
                    out = new Uri[clip.getItemCount()];
                    for (int k = 0; k < out.length; k++) out[k] = clip.getItemAt(k).getUri();
                } else if (data.getData() != null) out = new Uri[]{data.getData()};
            }
        }
        if (out == null) dropCameraUri();
        cameraUri = null;
        cb.onReceiveValue(out);
    }

    @Override
    public void onBackPressed() {
        if (web != null && web.canGoBack()) web.goBack();
        else moveTaskToBack(true);
    }

    @Override
    protected void onPause() {
        super.onPause();
        if (web != null && !bgKeep && !playKeep) web.onPause();
    }

    @Override
    protected void onResume() {
        super.onResume();
        if (web != null) web.onResume();
    }

    @Override
    protected void onDestroy() {
        try { stt.destroy(); } catch (Exception ignored) { }
        try { lstt.destroy(); } catch (Exception ignored) { }
        MicService.stop(this);
        PlayService.stop(this);
        try { tts.shutdown(); } catch (Exception ignored) { }
        try { llm.stop(); } catch (Exception ignored) { }
        try { models.cancelAll(); } catch (Exception ignored) { }
        if (web != null) { web.destroy(); web = null; }
        super.onDestroy();
    }
}
