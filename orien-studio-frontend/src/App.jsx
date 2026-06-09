import { useState } from "react";
import "./App.css";
import API from "./api";

function App() {

  const [url, setUrl] = useState("");

  const [hasCaptions, setHasCaptions] =
    useState(false);

  const [loading, setLoading] =
    useState(false);

  const [status, setStatus] =
    useState("");

  const [results, setResults] =
    useState(null);

  const processVideo = async () => {

    if (!url) {

      alert(
        "Please enter a YouTube URL"
      );

      return;
    }

    try {

      setLoading(true);

      setStatus(
        "Downloading Video..."
      );

      await API.post(
        "/download",
        {
          url: url
        }
      );

      setStatus(
        "Transcribing Video..."
      );

      await API.post(
        "/transcribe"
      );

      setStatus(
        "Finding Highlights..."
      );

      await API.post(
        "/highlights"
      );

      setStatus(
        "Refining Highlights..."
      );

      await API.post(
        "/refine-highlights"
      );

      setStatus(
        "Generating Clips..."
      );

      await API.post(
        "/generate-clips"
      );

      setStatus(
        "Generating Metadata..."
      );

      await API.post(
        "/generate-metadata"
      );

      if (!hasCaptions) {

        setStatus(
          "Generating Captions..."
        );

        await API.post(
          "/generate-captions"
        );

        setStatus(
          "Burning Captions..."
        );

        await API.post(
          "/burn-captions"
        );
      }

      setStatus(
        "Creating Vertical Shorts..."
      );

      await API.post(
        "/vertical-shorts"
      );

      setStatus(
        "Completed Successfully ✅"
      );

      const result =
        await API.get(
          "/results"
        );

      setResults(
        result.data
      );

    } catch (error) {

      console.error(error);

      setStatus(
        "Something went wrong ❌"
      );
    }

    setLoading(false);
  };

  return (

    <div className="app">

      <div className="hero">

        <h1>
          Orien Studio
        </h1>

        <h2>
          Turn Long Videos Into Viral Shorts With AI
        </h2>

        <p>
          Paste any YouTube video and
          automatically generate viral
          clips, captions and vertical
          shorts.
        </p>

        <input
          type="text"
          placeholder="Paste YouTube URL"
          value={url}
          onChange={(e) =>
            setUrl(
              e.target.value
            )
          }
        />

        <div className="checkbox">

          <input
            type="checkbox"
            id="captions"
            checked={hasCaptions}
            onChange={() =>
              setHasCaptions(
                !hasCaptions
              )
            }
          />

          <label htmlFor="captions">
            Video already has captions
          </label>

        </div>

        <button
          onClick={processVideo}
          disabled={loading}
        >

          {
            loading
              ? "Processing..."
              : "Generate Shorts"
          }

        </button>

        {

          status && (

            <div
              style={{
                marginTop: "25px",
                color: "#cbd5e1",
                fontSize: "18px"
              }}
            >

              {status}

            </div>

          )

        }

        {
          results && (

            <div
              style={{
                marginTop: "40px",
                width: "100%"
              }}
            >

              <h2
                style={{
                  color: "white",
                  marginBottom: "30px"
                }}
              >
                Generated Shorts
              </h2>

              {

                results.clips?.map(
                  (
                    clip,
                    index
                  ) => (

                    <div
                      key={index}
                      style={{
                        background:
                          "rgba(255,255,255,0.05)",

                        padding: "20px",

                        borderRadius: "20px",

                        marginBottom: "25px",

                        border:
                          "1px solid rgba(255,255,255,0.1)"
                      }}
                    >

                      <video
                        width="300"
                        controls
                        style={{
                          borderRadius:
                            "15px"
                        }}
                      >

                        <source
                          src={
                            `http://127.0.0.1:8000/clips/${clip}`
                          }
                          type="video/mp4"
                        />

                      </video>

                      <h3
                        style={{
                          color: "white",
                          marginTop: "15px"
                        }}
                      >
                        {
                          results.metadata?.[
                            index
                          ]?.title
                        }
                      </h3>

                      <p
                        style={{
                          color: "#cbd5e1"
                        }}
                      >
                        {
                          results.metadata?.[
                            index
                          ]?.caption
                        }
                      </p>

                      <p
                        style={{
                          color: "#60a5fa"
                        }}
                      >
                        {
                          results.metadata?.[
                            index
                          ]?.hashtags?.join(
                            " "
                          )
                        }
                      </p>

                      <a
                        href={
                          `http://127.0.0.1:8000/clips/${clip}`
                        }
                        download
                      >
                        <button
                          style={{
                            marginTop:
                              "10px"
                          }}
                        >
                          Download
                        </button>
                      </a>

                    </div>

                  )

                )

              }

            </div>

          )
        }

      </div>

    </div>

  );
}

export default App;