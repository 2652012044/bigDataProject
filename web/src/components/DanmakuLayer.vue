<template>
  <div ref="containerRef" class="danmaku-layer">
    <div
      v-for="item in danmakuItems"
      :key="item.id"
      class="danmaku-item"
      :style="{
        top: item.top + 'px',
        animationDuration: item.duration + 's',
        fontSize: item.fontSize + 'px',
        color: item.color,
      }"
    >
      {{ item.text }}
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'

const props = defineProps({
  messages: {
    type: Array,
    default: () => [
      '这本书太好看了!',
      '强烈推荐',
      '作者太厉害了',
      '追更中...',
      '神作!',
      '泪目了',
      '爷青回',
      '催更催更!',
      '五星好评',
    ],
  },
  speed: {
    type: Number,
    default: 8,
  },
  density: {
    type: Number,
    default: 3,
  },
})

const containerRef = ref(null)
const danmakuItems = ref([])

let idCounter = 0
let spawnTimer = null

const colors = [
  '#ffffff',
  '#ffd700',
  '#ff6b6b',
  '#69db7c',
  '#74c0fc',
  '#da77f2',
  '#ffa94d',
]

function getRandomItem(arr) {
  return arr[Math.floor(Math.random() * arr.length)]
}

function spawnDanmaku() {
  if (!containerRef.value || props.messages.length === 0) return

  const containerHeight = containerRef.value.offsetHeight
  if (containerHeight <= 0) return

  const count = Math.floor(Math.random() * props.density) + 1

  for (let i = 0; i < count; i++) {
    const id = ++idCounter
    const text = getRandomItem(props.messages)
    const top = Math.random() * (containerHeight - 30)
    const duration = props.speed + Math.random() * 4 - 2
    const fontSize = 14 + Math.floor(Math.random() * 4)
    const color = getRandomItem(colors)

    danmakuItems.value.push({ id, text, top, duration, fontSize, color })

    // Remove item after animation completes
    setTimeout(() => {
      const index = danmakuItems.value.findIndex((d) => d.id === id)
      if (index !== -1) {
        danmakuItems.value.splice(index, 1)
      }
    }, duration * 1000 + 500)
  }
}

onMounted(() => {
  // Initial spawn with slight delay
  setTimeout(() => {
    spawnDanmaku()
  }, 300)

  // Periodically spawn new danmaku
  spawnTimer = setInterval(() => {
    spawnDanmaku()
  }, 2000)
})

onUnmounted(() => {
  if (spawnTimer) {
    clearInterval(spawnTimer)
    spawnTimer = null
  }
  danmakuItems.value = []
})
</script>

<style lang="scss" scoped>
@use '@/assets/styles/variables' as *;

.danmaku-layer {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  overflow: hidden;
  pointer-events: none;
  z-index: 10;
}

.danmaku-item {
  position: absolute;
  white-space: nowrap;
  color: #fff;
  text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.6), 0 0 4px rgba(0, 0, 0, 0.3);
  font-weight: 500;
  opacity: 0.85;
  animation: danmaku-scroll linear forwards;
  right: 0;
  transform: translateX(100%);
}

@keyframes danmaku-scroll {
  0% {
    transform: translateX(100%);
    right: 0;
  }
  100% {
    transform: translateX(0);
    right: 100%;
  }
}
</style>
