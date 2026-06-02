<template>
  <div class="audio-player-container">
    <div class="audio-header">
      <h3 class="audio-title">
        <el-icon><Headset /></el-icon>
        录音播放器
      </h3>
      <div class="audio-info">
        <span class="duration">{{ formatTime(currentTime) }} / {{ formatTime(duration) }}</span>
      </div>
    </div>
    <div ref="waveformRef" class="waveform"></div>
    <div class="audio-controls">
      <el-button-group>
        <el-button @click="skipBackward">
          <el-icon><Back /></el-icon>
        </el-button>
        <el-button @click="togglePlay" :type="isPlaying ? 'danger' : 'primary'">
          <el-icon>
            <VideoPlay v-if="!isPlaying" />
            <VideoPause v-else />
          </el-icon>
        </el-button>
        <el-button @click="skipForward">
          <el-icon><Forward /></el-icon>
        </el-button>
      </el-button-group>
      <el-slider
        v-model="playbackRate"
        :min="0.5"
        :max="2"
        :step="0.1"
        class="rate-slider"
        @change="onRateChange"
      >
        <template #default="{ value }">
          <span class="rate-label">{{ value }}x</span>
        </template>
      </el-slider>
      <el-button @click="stop">
        <el-icon><VideoClose /></el-icon>
      </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch } from 'vue'
import WaveSurfer from 'wavesurfer.js'
import { Headset, Back, Forward, VideoPlay, VideoPause, VideoClose } from '@element-plus/icons-vue'

const props = defineProps<{
  audioUrl: string
  autoPlay?: boolean
}>()

const emit = defineEmits<{
  (e: 'timeupdate', time: number): void
  (e: 'ready', duration: number): void
  (e: 'play'): void
  (e: 'pause'): void
}>()

const waveformRef = ref<HTMLElement | null>(null)
const wavesurfer = ref<WaveSurfer | null>(null)
const isPlaying = ref(false)
const currentTime = ref(0)
const duration = ref(0)
const playbackRate = ref(1)

const initWaveSurfer = () => {
  if (!waveformRef.value) return

  wavesurfer.value = WaveSurfer.create({
    container: waveformRef.value,
    waveColor: '#409eff',
    progressColor: '#1890ff',
    cursorColor: '#f5222d',
    barWidth: 2,
    barGap: 3,
    barRadius: 2,
    height: 80,
    normalize: true
  })

  wavesurfer.value.load(props.audioUrl)

  wavesurfer.value.on('ready', () => {
    duration.value = wavesurfer.value?.getDuration() || 0
    emit('ready', duration.value)
    if (props.autoPlay) {
      wavesurfer.value?.play()
    }
  })

  wavesurfer.value.on('audioprocess', () => {
    currentTime.value = wavesurfer.value?.getCurrentTime() || 0
    emit('timeupdate', currentTime.value)
  })

  wavesurfer.value.on('play', () => {
    isPlaying.value = true
    emit('play')
  })

  wavesurfer.value.on('pause', () => {
    isPlaying.value = false
    emit('pause')
  })

  wavesurfer.value.on('finish', () => {
    isPlaying.value = false
  })
}

const togglePlay = () => {
  wavesurfer.value?.playPause()
}

const stop = () => {
  wavesurfer.value?.stop()
  isPlaying.value = false
  currentTime.value = 0
}

const skipBackward = () => {
  const current = wavesurfer.value?.getCurrentTime() || 0
  wavesurfer.value?.seekTo(Math.max(0, (current - 5) / duration.value))
}

const skipForward = () => {
  const current = wavesurfer.value?.getCurrentTime() || 0
  wavesurfer.value?.seekTo(Math.min(1, (current + 5) / duration.value))
}

const onRateChange = (rate: number) => {
  wavesurfer.value?.setPlaybackRate(rate)
}

const seekTo = (time: number) => {
  if (duration.value > 0) {
    wavesurfer.value?.seekTo(time / duration.value)
  }
}

const formatTime = (seconds: number): string => {
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
}

defineExpose({
  seekTo,
  togglePlay,
  stop
})

watch(() => props.audioUrl, (newUrl) => {
  if (wavesurfer.value && newUrl) {
    wavesurfer.value.load(newUrl)
  }
})

onMounted(() => {
  initWaveSurfer()
})

onUnmounted(() => {
  wavesurfer.value?.destroy()
})
</script>

<style scoped>
.audio-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.audio-title {
  margin: 0;
  font-size: 16px;
  display: flex;
  align-items: center;
  gap: 8px;
  color: #303133;
}

.audio-info {
  font-size: 14px;
  color: #909399;
  font-family: 'Courier New', monospace;
}

.waveform {
  margin-bottom: 16px;
  background: #f5f7fa;
  border-radius: 4px;
  padding: 8px;
}

.audio-controls {
  display: flex;
  align-items: center;
  gap: 16px;
}

.rate-slider {
  flex: 1;
  max-width: 200px;
}

.rate-label {
  font-size: 12px;
  color: #606266;
  font-weight: 600;
}
</style>
