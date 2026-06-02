<template>
  <div id="app">
    <el-container class="main-container">
      <el-header class="header">
        <div class="header-content">
          <h1 class="title">
            <el-icon :size="32" color="#409eff">
              <Microphone />
            </el-icon>
            方言保护田野调查总结会 - 乡音纪要
          </h1>
          <span class="subtitle">Dialect Preservation Field Survey Summary System</span>
        </div>
      </el-header>
      <el-main class="main-content">
        <router-view />
      </el-main>
      <el-footer class="footer">
        <span>© 2026 方言保护研究中心 | 乡音纪要系统</span>
      </el-footer>
    </el-container>
  </div>
</template>

<script setup lang="ts">
import { Microphone } from '@element-plus/icons-vue'
</script>

<style scoped>
.main-container {
  min-height: 100vh;
}

.header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  display: flex;
  align-items: center;
  padding: 0 40px;
}

.header-content {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.title {
  margin: 0;
  font-size: 24px;
  display: flex;
  align-items: center;
  gap: 12px;
}

.subtitle {
  font-size: 14px;
  opacity: 0.9;
}

.main-content {
  padding: 20px 40px;
  background: #f5f7fa;
}

.footer {
  background: #2c3e50;
  color: #ecf0f1;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
}
</style>
