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
  $: activeStream = "";
  $: oldActiveStream = "";
  let newData: {
    ready: boolean;
    name: string;
    isActive: boolean;
  }[] = [];
  let activePaths: string[] = [];
  onMount(() => {
    const fetchData = async () => {
      try {
        const activeStreamResponse = await fetch(
          "http://localhost:8000/api/v1/active_stream",
        );
        activeStream = (await activeStreamResponse.text()).replaceAll('"', "");
        // if (oldActiveStream !== null && oldActiveStream !== activeStream) {
        //   window.location.reload();
        // }
        oldActiveStream = activeStream;
        const pathListResponse = await (
          await fetch("http://localhost:9997/v3/paths/list")
        ).json();
        console.log(pathListResponse);
        newData = [];
        for (let i = 0; i < pathListResponse["items"].length; i++) {
          if (pathListResponse["items"][i]["ready"] === false) {
          }
          newData.push({
            name: pathListResponse["items"][i]["name"],
            ready: pathListResponse["items"][i]["ready"],
            isActive: pathListResponse["items"][i]["name"] === activeStream,
          });
        }
        console.log(newData);
        videos = Object.fromEntries(
          Object.entries(videos).filter(([_, v]) => v != null),
        );
        console.log(newData);
        if (JSON.stringify(newData) !== JSON.stringify(pathData)) {
          console.log("Data changed");
          pathData = newData;
          setTimeout(() => {
            for (const video in videos) {
              const hlsInstance = new hls({ backBufferLength: 2 });
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
  style="width: 100vw; height: 100vh; overflow: hidden; position: absolute; top: 0; left: 0"
>
  <div class="gradient"></div>
</div>
<h2 class="text-4xl text-center mt-4">OnBoard Live Design Stream</h2>
<img
  class="absolute top-0 left-0 w-64"
  src="https://assets.hackclub.com/flag-orpheus-left.svg"
  alt="Hack Club"
/>
<div
  class="grid w-screen grid-rows-2 grid-cols-1 h-[90vh] justify-items-center bg-transparent mt-0"
>
  {#if pathData?.map((path) => path.ready).includes(true)}
    {#if activePaths.length == 1}
      <!-- svelte-ignore a11y-media-has-caption -->
      <video
        controls
        autoplay
        id={activeStream}
        bind:this={videos[activeStream]}
        class="h-full w-auto"
      ></video>
    {:else}
      <div class="flex justify-center items-center w-auto h-[65vh] mt-5">
        {#each newData as path}
          {#if path.ready && path.name === activeStream}
            <!-- svelte-ignore a11y-media-has-caption -->
            <video
              controls
              autoplay
              id={path.name}
              bind:this={videos[path.name]}
              class="max-h-[65vh] w-auto bg-red-500"
            ></video>
          {/if}
        {/each}
      </div>

      <div
        class="flex items-center justify-center justify-items-center w-screen h-[25vh] bottom-12 absolute"
      >
        {#each newData as path}
          {#if path.name !== activeStream && path.ready}
            <!-- svelte-ignore a11y-media-has-caption -->
            <video
              controls
              autoplay
              muted
              id={path.name}
              bind:this={videos[path.name]}
              class="max-h-[25vh] mx-10"
            ></video>
          {/if}
        {/each}
      </div>
    {/if}
  {:else}
    <div class="text-center text-4xl absolute w-screen h-screen top-1/2">
      <p>
        No one is here yet!<br /> Check back later.
      </p>
    </div>
  {/if}
  <h2 class="absolute bottom-4 text-center w-screen text-3xl">
    Join at <div
      style="display: inline-block; color: #338eda; text-decoration-line: underline;"
    >
      https://hack.club/onboard-live
    </div>
  </h2>
</div>

<style>
  :root {
    overflow: hidden;
  }
  .gradient {
    width: 100vw;
    height: 100vh;
    position: absolute;
    transform-origin: center;
    overflow: hidden;
    z-index: -999;
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
