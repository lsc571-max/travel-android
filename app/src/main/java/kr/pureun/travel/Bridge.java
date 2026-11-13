package kr.pureun.travel;

import android.content.ClipData;
import android.content.ClipboardManager;
import android.content.ContentValues;
import android.content.Context;
import android.content.Intent;
import android.net.Uri;
import android.os.Build;
import android.os.Environment;
import android.provider.MediaStore;
import android.util.Base64;
import android.util.Log;
import android.webkit.JavascriptInterface;

import org.json.JSONObject;

import java.io.File;
import java.io.FileOutputStream;
import java.io.OutputStream;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/** 화면(JS)에서 부르는 창구. window.AndroidBridge.xxx() */
class Bridge {
    private final MainActivity act;
    private final ExecutorService llmPool = Executors.newSingleThreadExecutor();
    private OutputStream saveOut;
    private Uri saveUri;
    private String saveName = "";

    Bridge(MainActivity a) { act = a; }

    @JavascriptInterface
    public String info() {
        try {
            JSONObject o = new JSONObject();
            o.put("version", act.getPackageManager().getPackageInfo(act.getPackageName(), 0).versionName);
            o.put("sdk", Build.VERSION.SDK_INT);
            o.put("device", Build.MANUFACTURER + " " + Build.MODEL);
            o.put("stt", act.stt.available());
            o.put("sttOffline", act.stt.offlineAvailable());
            o.put("llmEngine", act.llm.available());
            return o.toString();
        } catch (Exception e) { return "{}"; }
    }

    // ── 음성 인식 ──
    @JavascriptInterface
    public void sttStart(final int sid, final String lang, final boolean continuous, final boolean preferOffline) {
        act.ui.post(new Runnable() { @Override public void run() { act.stt.start(sid, lang, continuous, preferOffline); } });
    }

    @JavascriptInterface
    public void sttStop(final int sid) {
        act.ui.post(new Runnable() { @Override public void run() { act.stt.stop(sid); } });
    }

    @JavascriptInterface
    public void sttAbort(final int sid) {
        act.ui.post(new Runnable() { @Override public void run() { act.stt.abort(sid); } });
    }

    // ── 목소리 ──
    @JavascriptInterface
    public String ttsVoices() { return act.tts.voices(); }

    @JavascriptInterface
    public void ttsSpeak(final int id, final String text, final String lang, final float rate, final String voice) {
        act.ui.post(new Runnable() { @Override public void run() { act.tts.speak(id, text, lang, rate, voice); } });
    }

    @JavascriptInterface
    public void ttsCancel() {
        act.ui.post(new Runnable() { @Override public void run() { act.tts.cancel(); } });
    }

    // ── 폰 안 번역 AI ──
    @JavascriptInterface
    public String llmState() { return act.llm.stateJson(); }

    @JavascriptInterface
    public void llmEnsure() {
        llmPool.execute(new Runnable() { @Override public void run() { act.llm.ensure(); } });
    }

    @JavascriptInterface
    public void llmStop() {
        llmPool.execute(new Runnable() { @Override public void run() { act.llm.stop(); } });
    }

    @JavascriptInterface
    public void llmChat(final int reqId, final String bodyJson) {
        llmPool.execute(new Runnable() {
            @Override public void run() {
                JSONObject o = new JSONObject();
                try {
                    o.put("id", reqId);
                    try {
                        o.put("text", act.llm.chat(bodyJson));
                        o.put("ok", true);
                    } catch (Throwable t) {
                        o.put("ok", false);
                        o.put("error", t.getMessage() == null ? t.getClass().getSimpleName() : t.getMessage());
                    }
                } catch (Exception ignored) { }
                act.emit("onLlm", o.toString());
            }
        });
    }

    @JavascriptInterface
    public String models() { return act.models.listJson(); }

    @JavascriptInterface
    public void modelDownload(String id) { act.models.download(id); }

    @JavascriptInterface
    public void modelCancel(String id) { act.models.cancel(id); }

    @JavascriptInterface
    public void modelDelete(final String id) {
        llmPool.execute(new Runnable() {
            @Override public void run() {
                boolean wasSelected = id.equals(act.models.selectedId());
                if (wasSelected) act.llm.stop();
                act.models.delete(id);
                act.emit("onLlmState", act.llm.stateJson());
            }
        });
    }

    @JavascriptInterface
    public void modelSelect(final String id) {
        llmPool.execute(new Runnable() {
            @Override public void run() { act.models.select(id); act.llm.ensure(); }
        });
    }

    @JavascriptInterface
    public String modelAdd(String name, String url) { return act.models.addCustom(name, url); }

    // ── 공유·복사·붙여넣기 ──
    @JavascriptInterface
    public void share(final String title, final String text) {
        act.ui.post(new Runnable() {
            @Override public void run() {
                try {
                    Intent i = new Intent(Intent.ACTION_SEND);
                    i.setType("text/plain");
                    i.putExtra(Intent.EXTRA_SUBJECT, title);
                    i.putExtra(Intent.EXTRA_TEXT, text);
                    act.startActivity(Intent.createChooser(i, title));
                } catch (Exception e) { Log.w(MainActivity.TAG, "share", e); }
            }
        });
    }

    @JavascriptInterface
    public void copy(final String text) {
        act.ui.post(new Runnable() {
            @Override public void run() {
                try {
                    ClipboardManager cm = (ClipboardManager) act.getSystemService(Context.CLIPBOARD_SERVICE);
                    cm.setPrimaryClip(ClipData.newPlainText("text", text));
                } catch (Exception ignored) { }
            }
        });
    }

    @JavascriptInterface
    public String paste() {
        try {
            ClipboardManager cm = (ClipboardManager) act.getSystemService(Context.CLIPBOARD_SERVICE);
            ClipData d = cm.getPrimaryClip();
            if (d == null || d.getItemCount() == 0) return "";
            CharSequence t = d.getItemAt(0).coerceToText(act);
            return t == null ? "" : t.toString();
        } catch (Throwable t) { return ""; }
    }

    // ── 파일 저장 (내려받기 폴더) : saveBegin → saveChunk… → saveEnd ──
    @JavascriptInterface
    public synchronized boolean saveBegin(String name, String mime) {
        try {
            saveAbort();
            saveName = name;
            if (Build.VERSION.SDK_INT >= 29) {
                ContentValues v = new ContentValues();
                v.put(MediaStore.Downloads.DISPLAY_NAME, name);
                v.put(MediaStore.Downloads.MIME_TYPE, mime == null || mime.isEmpty() ? "application/octet-stream" : mime);
                v.put(MediaStore.Downloads.IS_PENDING, 1);
                saveUri = act.getContentResolver().insert(MediaStore.Downloads.EXTERNAL_CONTENT_URI, v);
                saveOut = act.getContentResolver().openOutputStream(saveUri);
            } else {
                File d = act.getExternalFilesDir(Environment.DIRECTORY_DOWNLOADS);
                saveOut = new FileOutputStream(new File(d, name));
            }
            return saveOut != null;
        } catch (Throwable t) {
            Log.w(MainActivity.TAG, "save", t);
            saveAbort();
            return false;
        }
    }

    @JavascriptInterface
    public synchronized boolean saveChunk(String b64) {
        try {
            if (saveOut == null) return false;
            saveOut.write(Base64.decode(b64, Base64.DEFAULT));
            return true;
        } catch (Throwable t) { saveAbort(); return false; }
    }

    @JavascriptInterface
    public synchronized boolean saveEnd() {
        try {
            if (saveOut == null) return false;
            saveOut.close();
            saveOut = null;
            if (saveUri != null && Build.VERSION.SDK_INT >= 29) {
                ContentValues v = new ContentValues();
                v.put(MediaStore.Downloads.IS_PENDING, 0);
                act.getContentResolver().update(saveUri, v, null, null);
            }
            saveUri = null;
            return true;
        } catch (Throwable t) { saveAbort(); return false; }
    }

    private void saveAbort() {
        try { if (saveOut != null) saveOut.close(); } catch (Exception ignored) { }
        saveOut = null;
        if (saveUri != null) try { act.getContentResolver().delete(saveUri, null, null); } catch (Exception ignored) { }
        saveUri = null;
    }

    @JavascriptInterface
    public void keepAwake(boolean on) { act.keepAwake("js", on); }

    @JavascriptInterface
    public void openUrl(final String url) {
        act.ui.post(new Runnable() {
            @Override public void run() {
                try { act.startActivity(new Intent(Intent.ACTION_VIEW, Uri.parse(url))); } catch (Exception ignored) { }
            }
        });
    }
}
