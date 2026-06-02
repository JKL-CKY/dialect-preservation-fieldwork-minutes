<template>
  <div class="endangerment-level" :class="levelClass">
    <el-icon :size="16">
      <CircleCheck v-if="level === 'safe'" />
      <Warning v-else-if="level === 'vulnerable'" />
      <Alert v-else-if="level === 'definitely'" />
      <CircleClose v-else-if="level === 'severely'" />
      <BellFilled v-else-if="level === 'critically'" />
      <Delete v-else />
    </el-icon>
    <span>{{ levelText }}</span>
    <el-tag size="small" :type="tagType" effect="dark">
      {{ score }}/100
    </el-tag>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { CircleCheck, Warning, Alert, CircleClose, BellFilled, Delete } from '@element-plus/icons-vue'

const props = defineProps<{
  level: 'safe' | 'vulnerable' | 'definitely' | 'severely' | 'critically' | 'extinct'
  score: number
}>()

const levelText: Record<string, string> = {
  safe: '安全',
  vulnerable: '脆弱',
  definitely: '明显濒危',
  severely: '严重濒危',
  critically: '极度濒危',
  extinct: '已灭绝'
}

const levelClass = computed(() => `level-${props.level}`)

const tagType = computed(() => {
  const types: Record<string, 'success' | 'warning' | 'danger' | 'info'> = {
    safe: 'success',
    vulnerable: 'warning',
    definitely: 'warning',
    severely: 'danger',
    critically: 'danger',
    extinct: 'info'
  }
  return types[props.level] || 'info'
})
</script>
