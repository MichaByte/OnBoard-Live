<script lang="ts">
  import hls from "hls.js";
  import { onMount } from "svelte";
  let videos: { [key: string]: HTMLVideoElement } = {};
  let pathData:
    | {
        ready: boolean;
        name: string;
      }[]
    | null = null;
  let activeStream: string;
  let newData:
    | {
        bytesSent: any;
        bytesReceived: any;
        readyTime: any;
        ready: boolean;
        name: string;
      }[]
    | null = null;
  onMount(() => {
    const fetchData = async () => {
      try {
        const activeStreamResponse = await fetch(
          "http://localhost:8000/api/v1/active_stream",
        );
        activeStream = await activeStreamResponse.text();
        const pathListResponse = await fetch(
          "http://localhost:9997/v3/paths/list",
        );
        newData = (await pathListResponse.json())["items"];
        if (newData) {
          for (let i = 0; i < newData.length; i++) {
            delete newData[i].readyTime;
            delete newData[i].bytesReceived;
            delete newData[i].bytesSent;
          }
        }
        console.log(videos);
        videos = Object.fromEntries(
          Object.entries(videos).filter(([_, v]) => v != null),
        );

        if (JSON.stringify(newData) !== JSON.stringify(pathData)) {
          console.log("Data changed");
          pathData = newData;
          setTimeout(() => {
            for (const video in videos) {
              console.log(video);
              const hlsInstance = new hls({ progressive: false });
              hlsInstance.loadSource(
                `http://localhost:8888/${video}/index.m3u8`,
              );
              hlsInstance.attachMedia(videos[video]);
            }
          }, 5);
        }
      } catch (error) {
        console.error("Error fetching JSON data:", error);
      }
    };

    fetchData();

    const interval = setInterval(fetchData, 2000);

    return () => {
      // clearInterval(interval);
    };
  });
</script>

<div
  style="width: 100vw; height: 100vw; overflow: hidden; position: absolute; top: 0; left: 0"
>
  <div class="gradient"></div>
</div>
<div class="container2">
  <h2
    style="position: absolute; top: 0; width: 100vw; text-align: center;font-family: Arial, Helvetica, sans-serif;"
  >
    OnBoard Live Design Stream
  </h2>
  <img
    style="position: absolute; top: 0; left: 0; border: 0; width: 12vw; z-index: 999;"
    src="https://assets.hackclub.com/flag-orpheus-left.svg"
    alt="Hack Club"
  />
  {#if pathData?.map((path) => path.ready).includes(true)}
    <div class="container">
      {#each pathData as path}
        {#if path.ready}
          <!-- svelte-ignore a11y-media-has-caption -->
          <video
            controls
            autoplay
            id={path.name}
            bind:this={videos[path.name]}
            class:active={path.name === activeStream}
            class:video={Object.keys(videos).length > 1}
            class:only-video={!(Object.keys(videos).length > 1)}
          ></video>
        {/if}
      {/each}
    </div>
  {:else}
    <div class="container">
      <p
        style="text-align: center; font-size: 5vw; font-family: Arial, Helvetica, sans-serif"
      >
        No one is here yet!<br /> Check back later
      </p>
    </div>
  {/if}
  <h2
    style="position: absolute; bottom: 0; width: 100vw; text-align: center;font-family: Arial, Helvetica, sans-serif;"
  >
    Join at <div
      style="display: inline-block; color: #338eda; text-decoration-line: underline;"
    >
      https://hack.club/onboard-live
    </div>
  </h2>
</div>

<style>
  .container2 {
    display: flex;
    width: 100vw;
    height: 100vh;
    flex-wrap: wrap;
    position: absolute;
    top: 0;
    left: 0;
    background-color: transparent;
  }
  .gradient {
    width: 100vw;
    height: 100vh;
    position: absolute;
    transform-origin: center;
    overflow: hidden;
    background: linear-gradient(
      45deg,
      rgba(236, 55, 80, 1) 0%,
      rgba(255, 140, 55, 1) 25%,
      rgba(241, 196, 15, 1) 40%,
      rgba(51, 214, 166, 1) 60%,
      rgba(51, 142, 218, 1) 80%,
      rgba(166, 51, 214, 1) 100%
    );
    animation: move-gradient ease-in-out 15s infinite;
  }
  @keyframes move-gradient {
    0% {
      transform: scale(1) rotate(0deg);
    }
    25% {
      transform: scale(2) rotate(-35deg);
    }
    50% {
      transform: scale(3) rotate(90deg);
    }
    75% {
      transform: scale(2) rotate(-35deg);
    }
    100% {
      transform: scale(1) rotate(0deg);
    }
  }
  .video {
    width: 40vw;
    height: 40vh;
    padding-left: 10px;
    padding-right: 10px;
  }
  .only-video {
    width: 85vw;
    height: 85vh;
    padding-left: 10px;
    padding-right: 10px;
  }
  .active {
    width: 75vw;
    height: 75vh;
  }
  .container {
    align-items: center;
    display: flex;
    flex-wrap: wrap;
    justify-content: center;
    height: 100vh;
    width: 100vw;
  }
</style>
