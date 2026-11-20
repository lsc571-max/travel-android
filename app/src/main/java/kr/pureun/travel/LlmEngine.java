package kr.pureun.travel;

import android.util.Log;

import org.json.JSONObject;

import java.io.BufferedReader;
import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;

/**
 * 폰 안 번역 AI 엔진: 앱에 들어 있는 llama.cpp 서버(libllama_server.so)를
 * 이 휴대폰 안에서만(127.0.0.1) 띄우고, 번역 요청을 보낸다. 인터넷을 쓰지 않는다.
 */
class LlmEngine {
    static final String BIN = "libllama_server.so";
    static final int PORT = 18765;

    private final MainActivity act;
    private Process proc;
    private volatile String state = "idle";   // idle | loading | ready | error
    private volatile String error = "";
    private volatile String modelPath = "";
    private volatile int gen = 0;
    private final ArrayDeque<String> log = new ArrayDeque<>();

    LlmEngine(MainActivity a) { act = a; }

    File bin() { return new File(act.getApplicationInfo().nativeLibraryDir, BIN); }

    boolean available() { return bin().exists(); }

    String stateJson() {
        try {
            JSONObject o = new JSONObject();
            o.put("engine", available());
            o.put("state", state);
            o.put("error", error);
            o.put("model", act.models.selectedId("mt"));
            o.put("hasModel", act.models.selectedFile() != null);
            return o.toString();
        } catch (Exception e) { return "{}"; }
    }

    private void setState(String s, String err) {
        state = s; error = err == null ? "" : err;
        act.emit("onLlmState", stateJson());
    }

    /** 고른 모델로 엔진을 준비 (이미 준비됐으면 그대로) */
    synchronized void ensure() {
        File model = act.models.selectedFile();
        if (!available()) { setState("error", "이 설치 파일에는 번역 엔진이 들어 있지 않습니다"); return; }
        if (model == null) { setState("idle", ""); return; }
        if (("ready".equals(state) || "loading".equals(state)) && model.getAbsolutePath().equals(modelPath) && alive()) return;
        stopInternal();
        start(model);
    }

    private boolean alive() {
        try { return proc != null && proc.isAlive(); } catch (Throwable t) { return false; }
    }

    private void start(File model) {
        final int my = ++gen;
        modelPath = model.getAbsolutePath();
        synchronized (log) { log.clear(); }
        setState("loading", "");
        try {
            // 앞에 남아 있던 엔진이 있으면 끔 (앱이 갑자기 꺼졌던 경우)
            try { Runtime.getRuntime().exec(new String[]{"pkill", "-f", BIN}).waitFor(); } catch (Throwable ignored) { }
            int cores = Runtime.getRuntime().availableProcessors();
            int threads = Math.max(2, Math.min(5, cores - 3));   // S24 울트라(8코어) → 5 (소리 재생·화면이 쓸 코어를 남김)
            List<String> cmd = new ArrayList<>();
            cmd.add(bin().getAbsolutePath());
            cmd.add("-m"); cmd.add(modelPath);
            cmd.add("--host"); cmd.add("127.0.0.1");
            cmd.add("--port"); cmd.add(String.valueOf(PORT));
            cmd.add("-c"); cmd.add("4096");
            cmd.add("-t"); cmd.add(String.valueOf(threads));
            cmd.add("-np"); cmd.add("1");
            cmd.add("--no-webui");
            ProcessBuilder pb = new ProcessBuilder(cmd);
            pb.redirectErrorStream(true);
            pb.directory(act.getCacheDir());
            Map<String, String> env = pb.environment();
            env.put("LD_LIBRARY_PATH", act.getApplicationInfo().nativeLibraryDir);
            env.put("TMPDIR", act.getCacheDir().getAbsolutePath());
            env.put("HOME", act.getFilesDir().getAbsolutePath());
            final Process p = pb.start();
            proc = p;
            // 번역 엔진의 우선순위를 낮춤 → 통역 소리 재생이 항상 먼저 (소리가 끊기지 않게). 실패해도 그대로 진행
            try {
                java.util.regex.Matcher m = java.util.regex.Pattern.compile("pid=(\\d+)").matcher(String.valueOf(p));
                if (m.find()) android.os.Process.setThreadPriority(Integer.parseInt(m.group(1)), 10);
            } catch (Throwable ignored) { }
            new Thread(new Runnable() {
                @Override public void run() {
                    try (BufferedReader r = new BufferedReader(new InputStreamReader(p.getInputStream(), StandardCharsets.UTF_8))) {
                        String line;
                        while ((line = r.readLine()) != null) {
                            synchronized (log) { log.addLast(line); while (log.size() > 30) log.removeFirst(); }
                        }
                    } catch (Throwable ignored) { }
                }
            }, "llm-log").start();
            new Thread(new Runnable() {
                @Override public void run() { waitReady(p, my); }
            }, "llm-wait").start();
        } catch (Throwable t) {
            Log.w(MainActivity.TAG, "llm start", t);
            setState("error", "엔진을 시작하지 못했습니다: " + t.getMessage());
        }
    }

    private void waitReady(Process p, int my) {
        long end = System.currentTimeMillis() + 180000;
        while (my == gen && System.currentTimeMillis() < end) {
            boolean up;
            try { up = p.isAlive(); } catch (Throwable t) { up = false; }
            if (!up) {
                if (my == gen) setState("error", "엔진이 꺼졌습니다: " + tail());
                return;
            }
            try {
                HttpURLConnection c = (HttpURLConnection) new URL("http://127.0.0.1:" + PORT + "/health").openConnection();
                c.setConnectTimeout(1000); c.setReadTimeout(2000);
                int code = c.getResponseCode();
                c.disconnect();
                if (code == 200) { if (my == gen) setState("ready", ""); return; }
            } catch (Throwable ignored) { }
            try { Thread.sleep(400); } catch (InterruptedException e) { return; }
        }
        if (my == gen) setState("error", "엔진 준비 시간이 초과됐습니다: " + tail());
    }

    private String tail() {
        StringBuilder sb = new StringBuilder();
        synchronized (log) {
            int skip = Math.max(0, log.size() - 4), i = 0;
            for (String l : log) if (i++ >= skip) sb.append(l.length() > 160 ? l.substring(0, 160) : l).append(" / ");
        }
        return sb.toString();
    }

    private void stopInternal() {
        gen++;
        Process p = proc;
        proc = null;
        if (p != null) try { p.destroy(); } catch (Throwable ignored) { }
        modelPath = "";
        state = "idle"; error = "";
    }

    synchronized void stop() {
        stopInternal();
        act.emit("onLlmState", stateJson());
    }

    /** 번역 요청 (OpenAI 형식 본문). 엔진이 준비 중이면 최대 90초 기다림. 결과 글만 돌려줌 */
    String chat(String bodyJson) throws Exception { return chat(bodyJson, null); }

    /** onStart: 엔진 준비와 차례 기다림이 끝나 실제로 묻기 시작할 때 부름 (화면의 시간 제한은 이때부터 잼) */
    String chat(String bodyJson, Runnable onStart) throws Exception {
        if ("idle".equals(state) || "error".equals(state)) ensure();
        long end = System.currentTimeMillis() + 90000;
        while ("loading".equals(state) && System.currentTimeMillis() < end) Thread.sleep(200);
        if (!"ready".equals(state)) throw new Exception(error.isEmpty() ? "폰 AI가 준비되지 않았습니다" : error);
        HttpURLConnection c = (HttpURLConnection) new URL("http://127.0.0.1:" + PORT + "/v1/chat/completions").openConnection();
        boolean turn = Heavy.enter(60000);     // 받아 적기와 동시에 돌지 않게 차례를 기다림
        try {
            if (onStart != null) try { onStart.run(); } catch (Throwable ignored) { }
            c.setConnectTimeout(3000);
            c.setReadTimeout(180000);                       // 3분 안에 답이 없으면 시간 초과 (화면이 이유를 보여 줌)
            c.setRequestMethod("POST");
            c.setDoOutput(true);
            c.setRequestProperty("Content-Type", "application/json; charset=utf-8");
            byte[] body = bodyJson.getBytes(StandardCharsets.UTF_8);
            c.setFixedLengthStreamingMode(body.length);
            try (OutputStream os = c.getOutputStream()) { os.write(body); }
            int code = c.getResponseCode();
            InputStream in = code >= 400 ? c.getErrorStream() : c.getInputStream();
            ByteArrayOutputStream bo = new ByteArrayOutputStream();
            if (in != null) {
                byte[] buf = new byte[8192];
                int n;
                while ((n = in.read(buf)) > 0) bo.write(buf, 0, n);
                in.close();
            }
            String txt = new String(bo.toByteArray(), StandardCharsets.UTF_8);
            if (code != 200) throw new Exception("엔진 오류 " + code + " " + (txt.length() > 200 ? txt.substring(0, 200) : txt));
            JSONObject o = new JSONObject(txt);
            return o.getJSONArray("choices").getJSONObject(0).getJSONObject("message").optString("content", "");
        } finally {
            Heavy.done(turn);
            c.disconnect();
        }
    }
}
