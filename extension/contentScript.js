(() => {
  let youtubeLeftControls, youtubePlayer;

  const storeVideoDataAPI = async (youtubeUrl) => {
    try {
      const response = await fetch("http://127.0.0.1:5000/store_video_data", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          youtube_url: youtubeUrl,
        }),
      });

      if (!response.ok) {
        throw new Error(`Server responded with status ${response.status}`);
      }

      const data = await response.json();
      // console.log("Video data stored successfully:", data);

      return data;
    } catch (error) {
      console.error("Error sending video data:", error);
    }
  };

  const queryTimestampAPI = async (youtubeUrl, query) => {
    try {
      const response = await fetch("http://127.0.0.1:5000/query_timestamp", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          query_text: query,
          youtube_url: youtubeUrl,
        }),
      });

      if (!response.ok) {
        throw new Error(`Server responded with status ${response.status}`);
      }
      data = await response.json();
      const vidLocatorData =
        JSON.parse(sessionStorage.getItem("vidLocatorData")) || {};
      vidLocatorData.timestamps = data;
      sessionStorage.setItem("vidLocatorData", JSON.stringify(vidLocatorData));
      // console.log("Get timestamps", data);
      return data;
    } catch (error) {
      console.error("Error querying timestamps:", error);
    }
  };

  const renderTimestampList = (data) => {
    const modal = document.getElementById("vidlocator-modal");
    if (!modal) return;

    // clear old list (if any)
    const oldList = modal.querySelector("#timestamp-list");
    if (oldList) oldList.remove();

    const listContainer = document.createElement("div");
    listContainer.id = "timestamp-list";
    Object.assign(listContainer.style, {
      marginTop: "15px",
      padding: "10px",
      background: "#f1f1f1",
      borderRadius: "8px",
      overflowY: "auto",
      maxHeight: "150px",
    });

    const ul = document.createElement("ul");
    Object.assign(ul.style, {
      listStyle: "none",
      padding: "0",
      margin: "0",
      cursor: "pointer",
    });

    data.forEach((timestamp) => {
      const li = document.createElement("li");
      Object.assign(li.style, {
        padding: "8px 10px",
        marginBottom: "5px",
        backgroundColor: "#f2f2f2",
        borderRadius: "4px",
        boxShadow: "0 1px 3px rgba(0, 0, 0, 0.1)",
      });

      li.innerText = timestamp;

      li.addEventListener("click", () => {
        const video = document.querySelector("video");
        if (video) {
          video.currentTime = convertTimestampToSeconds(timestamp);
          video.play();
        } else {
          console.error("No video element found on the page!");
        }
      });

      ul.appendChild(li);
    });

    listContainer.appendChild(ul);
    modal.appendChild(listContainer);
  };

  const convertTimestampToSeconds = (timestamp) => {
    const [hours, minutes, seconds] = timestamp.split(":").map(Number);
    return hours * 3600 + minutes * 60 + seconds;
  };

  const vidLocatorModal = (youtubeUrl) => {
    // Check if the modal already exists
    if (document.getElementById("vidlocator-modal")) return;

    // Create modal container
    const modal = document.createElement("div");
    modal.id = "vidlocator-modal";
    Object.assign(modal.style, {
      display: "flex",
      flexDirection: "column",
      position: "fixed",
      top: "50%",
      left: "50%",
      transform: "translate(-50%, -50%)",
      zIndex: "1000",
      background: "#f9f9f9",
      paddingBottom: "20px",
      borderRadius: "8px",
      boxShadow: "0 8px 16px rgba(0, 0, 0, 0.3)",
      width: "480px",
      boxSizing: "border-box",
      fontFamily: "'Arial', sans-serif",
      maxHeight: "80vh", // Prevent modal from being too tall
      overflowY: "auto", // Allow scrolling if content overflows
    });

    // Create title
    const explain = document.createElement("p");
    explain.innerText = "Enter a query to receive recommended timestamps!";
    Object.assign(explain.style, {
      margin: "0 0 15px",
      fontSize: "18px",
      textAlign: "center",
      color: "#333",
    });

    const title = document.createElement("span");
    title.innerText = "VidLocator";
    Object.assign(title.style, {
      fontSize: "16px",
      fontWeight: "bold",
      color: "#333",
      padding: "5px 0px 0px 10px",
    });

    // Input field for user description
    const input = document.createElement("input");
    input.type = "text";
    input.placeholder = "Enter Query Text...";
    Object.assign(input.style, {
      width: "95%",
      padding: "10px",
      marginBottom: "15px",
      border: "1px solid #ccc",
      borderRadius: "4px",
      fontSize: "14px",
      boxSizing: "border-box",
      margin: "10px",
    });
    chrome.storage.session.setAccessLevel({ accessLevel: "TRUSTED_CONTEXTS" });
    const vidLocatorData =
      JSON.parse(sessionStorage.getItem("vidLocatorData")) || {};
    if (vidLocatorData && vidLocatorData.query_text) {
      input.value = vidLocatorData.query_text;
    }

    input.addEventListener("input", () => {
      vidLocatorData.query_text = input.value;
      sessionStorage.setItem("vidLocatorData", JSON.stringify(vidLocatorData));
    });

    // Button container (flexbox to center the buttons)
    const buttonContainer = document.createElement("div");
    Object.assign(buttonContainer.style, {
      display: "flex",
      justifyContent: "center", // Center buttons horizontally
      marginTop: "15px",
    });

    // Search button
    const submitBtn = document.createElement("button");
    submitBtn.innerText = "Search";
    Object.assign(submitBtn.style, {
      padding: "10px 15px",
      background: "#4CAF50",
      color: "#fff",
      border: "none",
      borderRadius: "4px",
      cursor: "pointer",
      fontSize: "14px",
    });
    submitBtn.addEventListener("click", () =>
      searchInput(youtubeUrl, input.value, modal)
    );

    // Close button (red rectangular button)
    const closeBtn = document.createElement("button");
    closeBtn.innerText = " X ";
    Object.assign(closeBtn.style, {
      background: "#f44336",
      color: "#fff",
      border: "none",
      padding: "5px 15px",
      borderTopRightRadius: "4px",
      cursor: "pointer",
      fontSize: "14px",
    });
    closeBtn.addEventListener("click", () => document.body.removeChild(modal));

    // Header with title and close button
    const header = document.createElement("div");
    Object.assign(header.style, {
      display: "flex",
      justifyContent: "space-between",
      alignItems: "center",
      marginBottom: "15px",
      borderBottom: "1px solid #ddd",
    });

    header.appendChild(title); 
    header.appendChild(closeBtn); 

    modal.appendChild(header); 
    modal.appendChild(explain);
    modal.appendChild(input);
    modal.appendChild(buttonContainer);
    buttonContainer.appendChild(submitBtn);

    document.body.appendChild(modal);
    if (vidLocatorData && vidLocatorData.timestamps) {
      renderTimestampList(vidLocatorData.timestamps);
    }
  };

  // Save user input with the current video timestamp
  const searchInput = (youtubeUrl, query_text, modal) => {
    if (!query_text) {
      alert("Please enter text!");
      return;
    }

    const submitBtn = modal.querySelector("button:first-child");
    submitBtn.innerText = "Loading...";
    submitBtn.disabled = true;

    queryTimestampAPI(youtubeUrl, query_text)
      .then((data) => {
        if (data) {
          renderTimestampList(data);
        } else {
          alert("VidLocator: No results found.");
        }
      })
      .catch((error) => {
        alert("An error occurred. Please try again.");
        console.error("Error:", error);
      })
      .finally(() => {
        submitBtn.innerText = "Search";
        submitBtn.disabled = false;
      });
  };

  // Handle new video load and setup features
  const handleNewVideo = async (youtubeUrl) => {
    await storeVideoDataAPI(youtubeUrl);

    const vidLocatorButton = document.getElementsByClassName("vidlocator-btn");
    if (vidLocatorButton.length === 0) {
      const controlContainer = document.createElement("div");
      controlContainer.style.display = "flex";
      controlContainer.style.alignItems = "center";
      controlContainer.style.marginRight = "10px";

      const searchBtn = document.createElement("img");
      searchBtn.src = chrome.runtime.getURL("assets/Search_Icon.png");
      searchBtn.className = "ytp-button vidlocator-btn";
      searchBtn.title = "Save timestamp";
      searchBtn.style.width = "30px";
      searchBtn.style.height = "auto";

      controlContainer.appendChild(searchBtn);
      youtubeLeftControls =
        document.getElementsByClassName("ytp-left-controls")[0];
      youtubePlayer = document.getElementsByClassName("video-stream")[0];

      youtubeLeftControls.appendChild(controlContainer);
      searchBtn.addEventListener("click", () => vidLocatorModal(youtubeUrl));
    }
  };

  // Handle messages from the extension
  chrome.runtime.onMessage.addListener((obj, sender, response) => {
    const { type, youtubeUrl } = obj;

    if (type === "NEW") {
      handleNewVideo(youtubeUrl);
    }
  });
})();
