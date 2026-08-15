
import {
  useEffect,
  useState
} from "react";
import "./App.css";
const VideoIcon = () => (
  <svg viewBox="0 0 24 24" aria-hidden="true">
    <rect
      x="3"
      y="6"
      width="12"
      height="12"
      rx="2"
    />
    <path d="M15 10l6-3v10l-6-3z" />
  </svg>
);

const AudioIcon = () => (
  <svg viewBox="0 0 24 24" aria-hidden="true">
    <path d="M9 18V6l10-2v12" />
    <circle cx="6" cy="18" r="3" />
    <circle cx="16" cy="16" r="3" />
  </svg>
);

const SubtitleIcon = () => (
  <svg viewBox="0 0 24 24" aria-hidden="true">
    <rect
      x="3"
      y="4"
      width="18"
      height="16"
      rx="2"
    />
    <path d="M7 10h10M7 14h6" />
  </svg>
);

const SparkleIcon = () => (
  <svg viewBox="0 0 24 24" aria-hidden="true">
    <path d="M12 2l1.8 6.2L20 10l-6.2 1.8L12 18l-1.8-6.2L4 10l6.2-1.8z" />
    <path d="M19 15l.8 2.2L22 18l-2.2.8L19 21l-.8-2.2L16 18l2.2-.8z" />
  </svg>
);

const DownloadIcon = () => (
  <svg viewBox="0 0 24 24" aria-hidden="true">
    <path d="M12 3v12" />
    <path d="M7 10l5 5 5-5" />
    <path d="M4 20h16" />
  </svg>
);

const CheckIcon = () => (
  <svg viewBox="0 0 24 24" aria-hidden="true">
    <path d="M5 12l4 4L19 6" />
  </svg>
);

const API_URL = "https://downly-2ykz.onrender.com";

function App() {
  const [url, setUrl] = useState("");
  const [video, setVideo] = useState(null);

  const [mode, setMode] = useState("video");

  const [selectedHeight, setSelectedHeight] =
    useState(null);

  const [audioQuality, setAudioQuality] =
    useState("192");

  const [loading, setLoading] =
    useState(false);

  const [downloading, setDownloading] =
    useState(false);

  const [progress, setProgress] =
    useState(0);

  const [downloadStatus, setDownloadStatus] =
    useState("");

  const [jobId, setJobId] =
    useState(null);

  const [error, setError] =
    useState("");


    // --------------------------------
// Subtitles
// --------------------------------

const [subtitlePanelOpen, setSubtitlePanelOpen] =
useState(false);

const [subtitleLoading, setSubtitleLoading] =
useState(false);

const [subtitleError, setSubtitleError] =
useState("");

const [subtitles, setSubtitles] =
useState([]);

const [selectedSubtitle, setSelectedSubtitle] =
useState(null);

const [subtitleSearch, setSubtitleSearch] =
  useState("");

  const [summaryLoading, setSummaryLoading] =
  useState(false);

const [summary, setSummary] =
  useState("");

const [summaryError, setSummaryError] =
  useState("");

const [summaryOpen, setSummaryOpen] =
  useState(false);

  const commonLanguages = [
    "en",
    "hi",
    "es",
    "fr",
    "de",
    "pt",
    "ja",
    "zh"
  ];
  
  const filteredSubtitles =
    subtitles.filter((item) => {
  
      const search =
        subtitleSearch
          .trim()
          .toLowerCase();
  
      // Nothing typed:
      // show only common languages
      if (!search) {
        return commonLanguages.includes(
          (item.language || "").toLowerCase()
        );
      }
  
      // User is searching:
      // search ALL available languages
      return (
        (item.name || "")
          .toLowerCase()
          .includes(search) ||
  
        (item.language || "")
          .toLowerCase()
          .includes(search)
      );
    });
const [subtitleDownloading, setSubtitleDownloading] =
useState(false);

    // --------------------------------
// Dark mode
// --------------------------------

const [darkMode, setDarkMode] =
useState(() => {
  return (
    localStorage.getItem(
      "downly-theme"
    ) === "dark"
  );
});

useEffect(() => {
localStorage.setItem(
  "downly-theme",
  darkMode
    ? "dark"
    : "light"
);
}, [darkMode]);

  // --------------------------------
  // Analyze video
  // --------------------------------

  const analyzeVideo = async () => {
    if (!url.trim()) {
      setError("Paste a YouTube URL first.");
      return;
    }

    setLoading(true);
    setError("");
    setVideo(null);
    setDownloadStatus("");
    setJobId(null);
    setProgress(0);

    try {
      const response = await fetch(
        `${API_URL}/api/info`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            url: url.trim(),
          }),
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail ||
          "Unable to analyze video."
        );
      }

      setVideo(data);

      // Get available video heights
      if (data.formats?.length) {
        const heights = [
          ...new Set(
            data.formats
              .map(
                (format) =>
                  format.height
              )
              .filter(Boolean)
          ),
        ].sort(
          (a, b) => b - a
        );

        setSelectedHeight(
          heights[0]
        );
      }
    } catch (err) {
      setError(
        err.message ||
        "Something went wrong."
      );
    } finally {
      setLoading(false);
    }
  };

  // --------------------------------
  // Format file size
  // --------------------------------

  const formatFileSize = (bytes) => {
    if (!bytes) {
      return "Size unavailable";
    }

    const units = [
      "B",
      "KB",
      "MB",
      "GB",
    ];

    let size = bytes;
    let unitIndex = 0;

    while (
      size >= 1024 &&
      unitIndex <
        units.length - 1
    ) {
      size /= 1024;
      unitIndex++;
    }

    return `${size.toFixed(1)} ${
      units[unitIndex]
    }`;
  };

  // --------------------------------
  // Quality label
  // --------------------------------

  const getQualityLabel = (
    height
  ) => {
    if (height >= 2160) {
      return "4K";
    }

    if (height >= 1440) {
      return "2K";
    }

    if (height >= 1080) {
      return "FHD";
    }

    if (height >= 720) {
      return "HD";
    }

    return "";
  };

  // --------------------------------
  // Get video qualities
  // --------------------------------

  const getVideoQualities = () => {
    if (!video?.formats) {
      return [];
    }

    const qualityMap = new Map();

    video.formats.forEach(
      (format) => {
        if (!format.height) {
          return;
        }

        const existing =
          qualityMap.get(
            format.height
          );

        // Prefer a format with filesize.
        if (
          !existing ||
          (
            !existing.filesize &&
            format.filesize
          )
        ) {
          qualityMap.set(
            format.height,
            format
          );
        }
      }
    );

    return Array.from(
      qualityMap.values()
    ).sort(
      (a, b) =>
        b.height - a.height
    );
  };

  // --------------------------------
  // Download completed file
  // --------------------------------

  const downloadFile = async (id) => {
    if (!id) {
      throw new Error(
        "Download job not found."
      );
    }
  
    setDownloadStatus(
      "Preparing browser download..."
    );
  
    const response = await fetch(
      `${API_URL}/api/download/${id}/file`
    );
  
    if (!response.ok) {
      let message =
        "Unable to download file.";
  
      try {
        const data =
          await response.json();
  
        message =
          data.detail || message;
      } catch {
        // Response was not JSON
      }
  
      throw new Error(message);
    }
  
    // Get the actual file as a Blob
    const blob =
      await response.blob();
  
    // Determine filename
    let filename =
      mode === "audio"
        ? "downly-audio.mp3"
        : "downly-video.mp4";
  
    const disposition =
      response.headers.get(
        "content-disposition"
      );
  
    if (disposition) {
      const filenameMatch =
        disposition.match(
          /filename\*=(?:UTF-8'')?([^;]+)/i
        );
  
      const normalFilenameMatch =
        disposition.match(
          /filename="?([^"]+)"?/i
        );
  
      if (filenameMatch?.[1]) {
        filename =
          decodeURIComponent(
            filenameMatch[1].trim()
          );
      } else if (
        normalFilenameMatch?.[1]
      ) {
        filename =
          normalFilenameMatch[1].trim();
      }
    }
  
    // Create temporary browser URL
    const objectUrl =
      window.URL.createObjectURL(
        blob
      );
  
    // Create invisible download link
    const link =
      document.createElement("a");
  
    link.href = objectUrl;
    link.download = filename;
  
    link.style.display = "none";
  
    document.body.appendChild(link);
  
    // Trigger browser download
    link.click();
  
    // Cleanup
    link.remove();
  
    window.URL.revokeObjectURL(
      objectUrl
    );
  
    setDownloadStatus(
      "Download complete!"
    );
  };

  // --------------------------------
// Subtitles
// --------------------------------

const handleSubtitleClick = async () => {

  if (!url.trim()) {
    setSubtitlePanelOpen(true);
    setSubtitleError(
      "Paste a YouTube URL first."
    );
    return;
  }

  setSubtitlePanelOpen(true);
  setSubtitleLoading(true);
  setSubtitleError("");
  setSubtitles([]);
  setSelectedSubtitle(null);

  try {

    const response = await fetch(
      `${API_URL}/api/subtitles`,
      {
        method: "POST",

        headers: {
          "Content-Type":
            "application/json",
        },

        body: JSON.stringify({
          url: url.trim(),
        }),
      }
    );

    const data =
      await response.json();

    if (!response.ok) {
      throw new Error(
        data.detail ||
        "Unable to find subtitles."
      );
    }

    if (
      !data.available ||
      !Array.isArray(data.subtitles) ||
      data.subtitles.length === 0
    ) {

      setSubtitleError(
        "No subtitles are available for this video."
      );

      return;
    }

    setSubtitles(
      data.subtitles
    );

    const english =
      data.subtitles.find(
        (item) =>
          item.language === "en" ||
          item.language
            ?.toLowerCase()
            .startsWith("en-")
      ) ||
      data.subtitles[0];

    setSelectedSubtitle(
      english
    );

  } catch (error) {

    console.error(
        "Analyze error:",
        error
    );

    let message =
        "Unable to analyze this video. Please try again.";

    if (error?.message) {

        const errorText =
            error.message.toLowerCase();

        if (
            errorText.includes(
                "sign in to confirm"
            ) ||
            errorText.includes(
                "not a bot"
            ) ||
            errorText.includes(
                "confirm you're not a bot"
            )
        ) {

            message =
                "YouTube is temporarily preventing this video from being accessed. Please try again in a moment.";

        } else if (
            errorText.includes(
                "invalid"
            ) ||
            errorText.includes(
                "url"
            )
        ) {

            message =
                "Please enter a valid YouTube URL.";

        } else {

            message =
                error.message;

        }
    }

    setError(message);

    // IMPORTANT:
    // Don't leave the UI in a loading state.

    setLoading(false);

    // Remove old result if analysis failed.

    setVideo(null);


  } finally {

    setSubtitleLoading(false);

  }
};


const handleSubtitleDownload =
  async () => {

    if (
      !selectedSubtitle?.language ||
      !url.trim()
    ) {
      return;
    }

    setSubtitleDownloading(true);
    setSubtitleError("");

    try {

      const response =
        await fetch(
          `${API_URL}/api/subtitles/download`,
          {
            method: "POST",

            headers: {
              "Content-Type":
                "application/json",
            },

            body: JSON.stringify({
              url: url.trim(),

              language:
                selectedSubtitle.language,
            }),
          }
        );

      if (!response.ok) {

        let data = {};

        try {
          data =
            await response.json();
        } catch {}

        throw new Error(
          data.detail ||
          "Unable to download subtitles."
        );
      }

      const blob =
        await response.blob();

      let filename =
        `downly-${selectedSubtitle.language}.srt`;

      const objectUrl =
        window.URL.createObjectURL(
          blob
        );

      const link =
        document.createElement("a");

      link.href = objectUrl;

      link.download =
        filename;

      document.body.appendChild(
        link
      );

      link.click();

      link.remove();

      window.URL.revokeObjectURL(
        objectUrl
      );

    } catch (err) {

      setSubtitleError(
        err.message ||
        "Unable to download subtitles."
      );

    } finally {

      setSubtitleDownloading(false);

    }
  };
  const handleSummaryClick = async () => {

    if (!url.trim()) {
      setError("Paste a YouTube URL first.");
      return;
    }
  
    setSummaryOpen(true);
    setSummaryLoading(true);
    setSummary("");
    setError("");
  
    try {
  
      const response = await fetch(
        `${API_URL}/api/summary`,
        {
          method: "POST",
  
          headers: {
            "Content-Type": "application/json",
          },
  
          body: JSON.stringify({
            url: url.trim(),
          }),
        }
      );
  
      const data =
        await response.json();
  
      console.log(
        "[AI SUMMARY RESPONSE]",
        data
      );
  
      if (!response.ok) {
  
        throw new Error(
          typeof data.detail === "string"
            ? data.detail
            : "AI Summary is currently unavailable."
        );
      }
  
      setSummary(
        data.summary || ""
      );
  
    } catch (err) {
  
      console.error(
        "[AI SUMMARY ERROR]",
        err
      );
  
      // USE THE EXISTING GLOBAL ERROR UI
      setError(
        err.message ||
        "AI Summary is currently unavailable. Please try again."
      );
  
      setSummaryOpen(true);
  
    } finally {
  
      setSummaryLoading(false);
  
    }
  };
  // --------------------------------
  // Start download
  // --------------------------------

  const startDownload = async () => {
    if (!video) {
      return;
    }

    if (
      mode === "video" &&
      !selectedHeight
    ) {
      setError(
        "Please select a video quality."
      );
      return;
    }

    if (
      mode === "audio" &&
      !audioQuality
    ) {
      setError(
        "Please select audio quality."
      );
      return;
    }

    setDownloading(true);
    setProgress(0);
    setError("");

    setDownloadStatus(
      "Preparing your download..."
    );

    setJobId(null);

    try {
      const requestBody =
        mode === "video"
          ? {
              url: url.trim(),
              mode: "video",
              height:
                selectedHeight,
              quality: null,
            }
          : {
              url: url.trim(),
              mode: "audio",
              height: null,
              quality:
                audioQuality,
            };

      const response =
        await fetch(
          `${API_URL}/api/download`,
          {
            method: "POST",
            headers: {
              "Content-Type":
                "application/json",
            },
            body: JSON.stringify(
              requestBody
            ),
          }
        );

      const data =
        await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail ||
          "Unable to start download."
        );
      }

      const id =
        data.job_id;

      setJobId(id);

      await monitorDownload(id);
    } catch (err) {
      setError(
        err.message ||
        "Download failed."
      );

      setDownloading(false);
    }
  };

  // --------------------------------
  // Monitor download
  // --------------------------------

  const monitorDownload =
    async (id) => {
      while (true) {
        try {
          const response =
            await fetch(
              `${API_URL}/api/download/${id}/status`
            );

          const data =
            await response.json();

          if (!response.ok) {
            throw new Error(
              data.detail ||
              "Unable to check download."
            );
          }

          const currentProgress =
            Number(
              data.progress || 0
            );

          setProgress(
            Math.min(
              currentProgress,
              100
            )
          );

          // Starting
          if (
            data.status ===
            "starting"
          ) {
            setDownloadStatus(
              "Preparing your download..."
            );
          }

          // Downloading
          else if (
            data.status ===
            "downloading"
          ) {
            setDownloadStatus(
              "Downloading your file..."
            );
          }

          // Processing
          else if (
            data.status ===
            "processing"
          ) {
            setDownloadStatus(
              "Finalizing your file..."
            );
          }

          // Completed
          else if (
            data.status ===
            "completed"
          ) {
            setProgress(100);

            setDownloadStatus(
              "Download complete!"
            );

            setDownloading(false);

// Show completed state first,
// then start the browser download.
              try {
                await new Promise((resolve) =>
                  setTimeout(resolve, 350)
                );

                await downloadFile(id);
              } catch (err) {
                setError(
                  err.message ||
                  "Unable to save downloaded file."
                );
              }


            return;
          }

          // Failed
          else if (
            data.status ===
            "failed"
          ) {
            throw new Error(
              data.error ||
              "Download failed."
            );
          }

          await new Promise(
            (resolve) =>
              setTimeout(
                resolve,
                1000
              )
          );
        } catch (err) {
          setError(
            err.message ||
            "Download failed."
          );

          setDownloading(false);

          return;
        }
      }
    };

  // --------------------------------
  // Reset
  // --------------------------------

  const reset = () => {
    setUrl("");
    setVideo(null);
    setJobId(null);
    setProgress(0);
    setDownloadStatus("");
    setError("");
    setMode("video");
    setSelectedHeight(null);
    setAudioQuality("192");
  };

  // --------------------------------
  // UI
  // --------------------------------

  return (
      
        <div
          className={
            darkMode
              ? "app dark"
              : "app"
          }
        >

      {/* =========================
          NAVBAR
      ========================== */}

<nav className="navbar">

<div
  className="brand"
  onClick={() => {
    reset();

    window.scrollTo({
      top: 0,
      behavior: "smooth",
    });
  }}
  role="button"
  tabIndex={0}
  onKeyDown={(event) => {
    if (
      event.key === "Enter" ||
      event.key === " "
    ) {
      reset();

      window.scrollTo({
        top: 0,
        behavior: "smooth",
      });
    }
  }}
>
  <div className="brand-icon">
    D
  </div>

  <span>
    Downly
  </span>
</div>


<div className="nav-actions">

  <span className="nav-badge">
    Free & Open Source
  </span>


  <button
    className="theme-toggle"
    onClick={() =>
      setDarkMode(
        (previous) =>
          !previous
      )
    }
    aria-label={
      darkMode
        ? "Switch to light mode"
        : "Switch to dark mode"
    }
    title={
      darkMode
        ? "Light mode"
        : "Dark mode"
    }
  >

    <span className="theme-icon">
      {darkMode
        ? "☀️"
        : "🌙"}
    </span>

    <span className="theme-label">
      {darkMode
        ? "Light"
        : "Dark"}
    </span>

  </button>

</div>

</nav>


      <main className="main">

        {/* =========================
            HERO
        ========================== */}

        {!video && (
          <section className="hero">

            <div className="hero-badge">
              ⚡ Fast & Simple
            </div>

            <h1>
              Download videos.
              <br />
              <span>
                Keep them yours.
              </span>
            </h1>

            <p>
              Download YouTube videos
              and audio in your
              preferred quality.
            </p>

          </section>
        )}


        {/* =========================
            DOWNLOADER CARD
        ========================== */}

        <section className="downloader-card">

          {/* URL INPUT */}

          <div className="url-row">

            <div className="url-input">

              <span className="url-icon">
                🔗
              </span>

              <input
                type="text"
                placeholder="Paste YouTube URL here..."
                value={url}
                onChange={(e) =>
                  setUrl(
                    e.target.value
                  )
                }
                disabled={
                  loading ||
                  downloading
                }
                onKeyDown={(e) => {
                  if (
                    e.key ===
                    "Enter"
                  ) {
                    analyzeVideo();
                  }
                }}
              />

              {url && (
                <button
                  className="clear"
                  onClick={() =>
                    setUrl("")
                  }
                  disabled={
                    loading ||
                    downloading
                  }
                  aria-label="Clear URL"
                >
                  
                </button>
              )}

            </div>

            <button
              className="analyze-button"
              onClick={
                analyzeVideo
              }
              disabled={
                loading ||
                downloading
              }
            >
              {loading ? (
                <>
                  <span className="button-spinner" />
                  Analyzing...
                </>
              ) : (
                <>
                  Analyze
                  <span className="button-arrow">
                    →
                  </span>
                </>
              )}
            </button>

          </div>


          {/* ERROR */}

          {error && (
            <div className="error">

              <span className="error-icon">
                ⚠
              </span>

              <span>
                {error}
              </span>

            </div>
          )}


          {/* =========================
              VIDEO RESULT
          ========================== */}

          {video && (
            <div className="result">

              {/* VIDEO PREVIEW */}

              <div className="video-preview">

                <div className="thumbnail-wrapper">

                  <img
                    src={
                      video.thumbnail
                    }
                    alt={
                      video.title
                    }
                  />

                  <div className="youtube-badge">
                    YOUTUBE
                  </div>

                  {video.duration_formatted && (
                    <div className="duration-badge">
                      ◷{" "}
                      {
                        video.duration_formatted
                      }
                    </div>
                  )}

                  <div className="thumbnail-play">
                    ▶
                  </div>

                </div>


                <div className="video-details">

                  <div className="verified-badge">
                    ✓ Verified Video Stream
                  </div>

                  <h2>
                    {video.title}
                  </h2>

                  <div className="metadata">

                    <span>
                      👤{" "}
                      {video.uploader ||
                        "Unknown"}
                    </span>

                    <span>
                      ◷{" "}
                      {
                        video.duration_formatted
                      }
                    </span>

                    <span>
                      👁{" "}
                      {video.view_count
                        ? video.view_count.toLocaleString()
                        : "—"}{" "}
                      views
                    </span>

                  </div>

                </div>

              </div>


              <div className="divider" />


              {/* FORMAT */}

              <div className="format-heading-row">

                <div className="format-title">
                  Choose your format
                </div>

                <div className="engine-label">
                  ⚡ Fast Engine
                </div>

              </div>


              <div className="format-tabs">

                {/* VIDEO */}
            

                <button
                  className={
                    mode === "video" && !subtitlePanelOpen
                      ? "format-tab active"
                      : "format-tab"
                  }
                  onClick={() => {
                    setMode("video");
                    setSubtitlePanelOpen(false);
                    setSelectedSubtitle(null);
                    setSubtitleError("");
                  }}
                  disabled={
                    downloading
                  }
                >

                  <span className="format-icon">
                    <VideoIcon />
                  </span>

                  <span className="format-content">

                    <strong>
                      Video
                    </strong>

                    <small>
                      MP4 format • Up to 4K
                    </small>

                  </span>

                  {mode === "video" && !subtitlePanelOpen && (
                    <span className="selected-check">
                      ✓
                    </span>
                  )}

                </button>


                {/* AUDIO */}

                <button
                  className={
                    mode === "audio" && !subtitlePanelOpen
                      ? "format-tab active"
                      : "format-tab"
                  }
                  onClick={() => {
                    setMode("audio");
                    setSubtitlePanelOpen(false);
                    setSelectedSubtitle(null);
                    setSubtitleError("");
                  }}
                  disabled={
                    downloading
                  }
                >

                  <span className="format-icon">
                    🎵
                  </span>

                  <span className="format-content">

                    <strong>
                      Audio
                    </strong>

                    <small>
                      MP3 format
                    </small>

                  </span>

                  {mode === "audio" && !subtitlePanelOpen && (
                    <span className="selected-check">
                      ✓
                    </span>
                  )}

                </button>


               {/* SUBTITLES */}

<button
  type="button"
  className={`format-tab subtitle-format ${
    subtitlePanelOpen
      ? "active"
      : ""
  }`}
  onClick={
    handleSubtitleClick
  }
  disabled={
    subtitleLoading ||
    downloading
  }
>

  <span className="format-icon">
    <SubtitleIcon />
  </span>

  <span className="format-content">

    <strong>
      Subtitles
    </strong>

    <small>
      {subtitleLoading
        ? "Finding captions..."
        : "SRT / VTT files"}
    </small>

  </span>

  <span className="format-action">

    {subtitleLoading ? (
      <span className="mini-spinner" />
    ) : (
      <span className="format-arrow">
        →
      </span>
    )}

  </span>

</button>


                {/* AI SUMMARY */}

                <button
  type="button"
  className={
    mode === "summary"
      ? "format-tab ai-format active"
      : "format-tab ai-format"
  }
  onClick={handleSummaryClick}
  disabled={summaryLoading}
>
  <span className="format-icon">
    ✨
  </span>

  <span>
    <strong>
      AI Summary
    </strong>

    <small> <span>
      {summaryLoading
        ? "Generating...":"feat. Gemini AI"}</span>
    </small>
  </span>

  <span className="ai-new-badge">
    NEW
  </span>
</button>

               

              </div>

{/* =========================
    SUBTITLE PANEL
========================== */}

{subtitlePanelOpen && (
  <div className="subtitle-panel">

    <div className="subtitle-panel-header">

      <div>

        <div className="subtitle-panel-title">

          <span className="subtitle-panel-icon">
            <SubtitleIcon />
          </span>

          <span>
            Available subtitles
          </span>

        </div>

        <p>
          Select a caption language to download.
        </p>

      </div>

      <button
        type="button"
        className="subtitle-close"
        onClick={() => {
          setSubtitlePanelOpen(false);
          setSubtitleError("");
        }}
      >
        
      </button>

    </div>


    {subtitleLoading && (
      <div className="subtitle-loading">

        <span className="mini-spinner" />

        <span>
          Finding available captions...
        </span>

      </div>
    )}


    {!subtitleLoading && subtitleError && (
      <div className="subtitle-error">

        <span className="subtitle-error-icon">
          !
        </span>

        <span>
          {subtitleError}
        </span>

      </div>
    )}


    {!subtitleLoading &&
      !subtitleError &&
      subtitles.length > 0 && (

      <>


            
            

            {filteredSubtitles.length === 0 && (
        <div className="subtitle-no-results">
          No languages found.
        </div>
      )}

<div className="subtitle-search">

  <span className="subtitle-search-icon">
    🔍
  </span>

  <input
    type="text"
    placeholder="Search language..."
    value={subtitleSearch}
    onChange={(e) =>
      setSubtitleSearch(e.target.value)
    }
  />

  {subtitleSearch && (
    <button
      type="button"
      className="subtitle-search-clear"
      onClick={() =>
        setSubtitleSearch("")
      }
    >
      
    </button>
  )}

</div>

        <div className="subtitle-list">

          {filteredSubtitles.map((item, index) => {

            const language =
              item.language ||


              item.lang ||
              `Language ${index + 1}`;

            const selected =
              selectedSubtitle === item;

            return (
              <button
                key={`${language}-${index}`}
                type="button"
                className={`subtitle-option ${
                  selected ? "selected" : ""
                }`}
                onClick={() =>
                  setSelectedSubtitle(item)
                }
              >

                <span className="subtitle-language-icon">
                  {language
                    .slice(0, 2)
                    .toUpperCase()}
                </span>

                <span className="subtitle-option-content">

                
                <strong>
                {item.name || language}
                </strong>

                  <small>
                    {item.automatic
                      ? "Auto-generated captions"
                      : "Provided captions"}
                  </small>

                </span>

                <span className="subtitle-option-check">

                  {selected ? (
                    <CheckIcon />
                  ) : (
                    "→"
                  )}

                </span>

              </button>
            );

          })}

        </div>


        <button
          type="button"
          className="subtitle-download-button"
          disabled={
            !selectedSubtitle ||
            subtitleDownloading
          }
          onClick={
            handleSubtitleDownload
          }
        >

          <DownloadIcon />

          {subtitleDownloading
            ? "Preparing subtitle..."
            : `Download ${
                selectedSubtitle?.language ||
                "selected"
              } subtitle`}

        </button>

      </>

    )}

  </div>
)}
              {/* =========================
                  VIDEO QUALITY
              ========================== */}

              {mode === "video" ? (

                <div className="quality-section">

                  <div className="quality-label">
                    Select Video Resolution:
                  </div>

                  <div className="quality-grid">

                    {getVideoQualities().map(
                      (format) => {

                        const label =
                          getQualityLabel(
                            format.height
                          );

                        return (
                          <button
                            key={
                              format.height
                            }
                            className={
                              selectedHeight ===
                              format.height
                                ? "quality active"
                                : "quality"
                            }
                            onClick={() =>
                              setSelectedHeight(
                                format.height
                              )
                            }
                            disabled={
                              downloading
                            }
                          >

                            <div className="quality-top">

                              <strong>
                                {
                                  format.height
                                }p
                              </strong>

                              {label && (
                                <span className="quality-badge">
                                  {label}
                                </span>
                              )}

                            </div>

                            <span>
                              MP4
                              {" • "}
                              {
                                formatFileSize(
                                  format.filesize
                                )
                              }
                            </span>

                          </button>
                        );
                      }
                    )}

                  </div>

                </div>

              ) : (

                /* AUDIO QUALITY */

                <div className="quality-section">

                  <div className="quality-label">
                    Select Audio Quality:
                  </div>

                  <div className="audio-quality">

                    {[
                      "320",
                      "192",
                      "128",
                    ].map(
                      (quality) => (

                        <button
                          key={
                            quality
                          }
                          className={
                            audioQuality ===
                            quality
                              ? "quality active"
                              : "quality"
                          }
                          onClick={() =>
                            setAudioQuality(
                              quality
                            )
                          }
                          disabled={
                            downloading
                          }
                        >

                          <div className="quality-top">

                            <strong>
                              {quality}
                            </strong>

                            {quality ===
                              "320" && (
                              <span className="quality-badge">
                                BEST
                              </span>
                            )}

                          </div>

                          <span>
                            kbps • MP3
                          </span>

                        </button>

                      )
                    )}

                  </div>

                </div>

              )}


              {/* =========================
                  DOWNLOAD BUTTON
              ========================== */}

              <button
                className={
                  downloading
                    ? "download-button downloading"
                    : "download-button"
                }
                onClick={
                  startDownload
                }
                disabled={
                  downloading
                }
              >

                {downloading ? (
                  <>
                    <span className="download-spinner" />
                    {downloadStatus ||
                      "Downloading..."}
                  </>
                ) : (
                  <>
                    <span className="download-icon">
                      <DownloadIcon />
                    </span>

                    Download{" "}
                    {mode === "video"
                      ? `Video (${selectedHeight}p)`
                      : `Audio (${audioQuality} kbps)`}
                  </>
                )}

              </button>


              {/* =========================
                  PROGRESS
              ========================== */}

              {downloading && (
                <div className="progress-container">

                  <div className="progress-info">

                    <span>
                      {downloadStatus}
                    </span>

                    <strong>
                      {progress.toFixed(
                        1
                      )}
                      %
                    </strong>

                  </div>

                  <div className="progress-track">

                    <div
                      className="progress-fill"
                      style={{
                        width:
                          `${progress}%`,
                      }}
                    />

                  </div>

                </div>
              )}


              {/* =========================
                  COMPLETE
              ========================== */}

              {!downloading &&
                downloadStatus ===
                  "Download complete!" && (

                <div className="completed">

                  <div className="completed-icon">
                    ✓
                  </div>

                  <div className="completed-content">

                    <strong>
                      Download complete
                    </strong>

                    <span>
                      Your file is ready and
                      has been sent to the browser.
                    </span>

                  </div>

                </div>
              )}

            </div>
          )}

        </section>


        {/* NEW DOWNLOAD */}

        {video && (
          <button
            className="new-download"
            onClick={
              reset
            }
            disabled={
              downloading
            }
          >
            <span>
              ↻
            </span>

            Download another video
          </button>
        )}

      </main>


      {/* FOOTER */}

      <footer>
        <span>
          Downly
        </span>
        {" • "}
        Built for learning
      </footer>

    </div>
  );
}

export default App;