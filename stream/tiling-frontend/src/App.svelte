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
  let oldActiveStream: string | null = null;
  let newData:
    | {
        bytesSent: any;
        bytesReceived: any;
        readyTime: any;
        ready: boolean;
        name: string;
      }[]
    | null = null;
  let activePaths: string[] = [];
  onMount(() => {
    const fetchData = async () => {
      try {
        const activeStreamResponse = await fetch(
          "http://localhost:8000/api/v1/active_stream",
        );
        activeStream = (await activeStreamResponse.text()).replaceAll('"', "");
        if (oldActiveStream !== null && oldActiveStream !== activeStream) {
          window.location.reload();
        }
        oldActiveStream = activeStream;
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
        videos = Object.fromEntries(
          Object.entries(videos).filter(([_, v]) => v != null),
        );

        if (JSON.stringify(newData) !== JSON.stringify(pathData)) {
          console.log("Data changed");
          pathData = newData;
          for (let pathIdx = 0; pathIdx < pathData?.length! - 1; pathIdx++) {
            if (pathData![pathIdx].ready) {
              activePaths.push(pathData![pathIdx].name);
            }
          }
          setTimeout(() => {
            for (const video in videos) {
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
<div
  class="flex w-screen h-screen justify-items-center bg-transparent absolute top-0 left-0 overflow-hidden"
>
  <h2 class="text-4xl text-center w-screen absolute top-4">
    OnBoard Live Design Stream
  </h2>
  <img
    class="absolute top-0 left-0 w-48"
    src="https://assets.hackclub.com/flag-orpheus-left.svg"
    alt="Hack Club"
  />
  {#if pathData?.map((path) => path.ready).includes(true)}
    {#if activePaths.length == 1}
      <div
        class="flex justify-center items-center w-screen h-3/4 absolute top-20"
      >
        <!-- svelte-ignore a11y-media-has-caption -->
        <video
          controls
          autoplay
          id={activeStream}
          bind:this={videos[activeStream]}
          class="h-full w-auto"
        ></video>
      </div>
    {:else}
      <div
        class="flex justify-center items-center w-screen h-1/2 absolute top-20"
      >
        <!-- svelte-ignore a11y-media-has-caption -->
        <video
          controls
          autoplay
          id={activeStream}
          bind:this={videos[activeStream]}
          class="h-full w-auto"
        ></video>
      </div>
      <div
        class="flex justify-center items-center w-screen h-1/4 absolute bottom-10"
      >
        {#each activePaths as path}
          {#if path !== activeStream}
            <!-- svelte-ignore a11y-media-has-caption -->
            <video
              controls
              autoplay
              muted
              id={path}
              bind:this={videos[path]}
              class="h-[20vh] w-auto mx-10"
            ></video>
          {/if}
        {/each}
      </div>
    {/if}
  {:else}
    <div class="text-center text-4xl absolute w-screen h-screen top-1/2">
      <p>
        No one is here yet!<br /> Check back later
      </p>
    </div>
  {/if}
  <h2 class="absolute bottom-4 text-center w-screen text-xl">
    Join at <div
      style="display: inline-block; color: #338eda; text-decoration-line: underline;"
    >
      https://hack.club/onboard-live
    </div>
  </h2>
</div>

<style>
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
  /* .video {
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
    width: 60% !important;
    height: 60% !important;
  }
  .container {
    align-items: center;
    display: flex;
    flex-wrap: wrap;
    justify-content: center;
    height: 100vh;
    width: 100vw;
  } */
</style>
