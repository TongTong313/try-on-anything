<template>
  <div class="app-container">
    <!-- 顶部导航栏 -->
    <header class="app-header">
      <div class="header-left">
        <h1 class="app-title">{{ $t('common.appName') }}</h1>
      </div>
      <nav class="header-nav">
        <router-link to="/" class="nav-link">{{ $t('nav.home') }}</router-link>
        <router-link to="/settings" class="nav-link">{{ $t('nav.settings') }}</router-link>
      </nav>
      <div class="header-right">
        <ThemeSwitcher />
      </div>
    </header>

    <!-- 主内容区域 -->
    <main class="app-main">
      <router-view />
    </main>
  </div>
</template>

<script setup>
import ThemeSwitcher from './components/ThemeSwitcher.vue'
</script>

<style scoped>
.app-container {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.app-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 32px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.header-left {
  flex: 1;
}

.app-title {
  margin: 0;
  font-size: 24px;
  font-weight: 600;
  color: white;
}

.header-nav {
  display: flex;
  gap: 24px;
  justify-content: center;
  flex-shrink: 0;
}

.header-right {
  flex: 1;
  display: flex;
  justify-content: flex-end;
  align-items: center;
}

.nav-link {
  color: white;
  text-decoration: none;
  font-size: 16px;
  font-weight: 500;
  padding: 8px 16px;
  border-radius: 4px;
  transition: all 0.3s;
  white-space: nowrap;
}

.nav-link:hover {
  background: rgba(255, 255, 255, 0.1);
}

.nav-link.router-link-active {
  background: rgba(255, 255, 255, 0.2);
}

.app-main {
  flex: 1;
  padding: 20px;
}
</style>

<!-- 暗色模式全局样式（不使用 scoped） -->
<style>
/* 暗色模式适配 */
html.dark {
  background-color: #1a1a1a;
  color: #f5f5f5;
}

html.dark .app-container {
  background-color: #1a1a1a;
  color: #f5f5f5;
}

html.dark .app-header {
  background: linear-gradient(135deg, #4a5568 0%, #2d3748 100%);
}

html.dark .app-main {
  background-color: #1a1a1a;
}

/* Element Plus 组件深色模式适配 */

/* Alert 提示框 */
html.dark .el-alert {
  background-color: #374151;
  border-color: #4a5568;
}

html.dark .el-alert .el-alert__title {
  color: #f5f5f5;
}

html.dark .el-alert .el-alert__description {
  color: #e5e7eb;
}

html.dark .el-alert--info.is-light {
  background-color: #1e3a5f;
  border-color: #2563eb;
}

html.dark .el-alert--info.is-light .el-alert__description {
  color: #93c5fd;
}

/* Upload 上传组件 */
html.dark .el-upload-dragger {
  background-color: #374151 !important;
  border-color: #4a5568 !important;
}

html.dark .el-upload-dragger:hover {
  border-color: #60a5fa !important;
}

/* Card 卡片 */
html.dark .el-card {
  background-color: #2d3748;
  border-color: #4a5568;
}

html.dark .el-card__header {
  border-bottom-color: #4a5568;
}

/* Input 输入框 */
html.dark .el-input__wrapper {
  background-color: #374151;
  box-shadow: 0 0 0 1px #4a5568 inset;
}

html.dark .el-input__inner {
  color: #f5f5f5;
}

html.dark .el-input__inner::placeholder {
  color: #d1d5db;
}

/* Select 选择器 */
html.dark .el-select__wrapper {
  background-color: #374151;
  box-shadow: 0 0 0 1px #4a5568 inset;
}

/* Radio 单选框 */
html.dark .el-radio-button__inner {
  background-color: #374151;
  border-color: #4a5568;
  color: #f5f5f5;
}

html.dark .el-radio-button__original-radio:checked + .el-radio-button__inner {
  background-color: #409eff;
  border-color: #409eff;
}

/* Tabs 标签页 */
html.dark .el-tabs__item {
  color: #d1d5db;
}

html.dark .el-tabs__item.is-active {
  color: #60a5fa;
}

/* Divider 分割线 */
html.dark .el-divider__text {
  background-color: #2d3748;
  color: #f5f5f5;
}

/* Form 表单 */
html.dark .el-form-item__label {
  color: #f5f5f5;
}

/* Card Header 卡片标题 */
html.dark .card-header h2 {
  color: #f5f5f5;
}
</style>
