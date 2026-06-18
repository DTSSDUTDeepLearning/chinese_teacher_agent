<template>
  <a-layout style="min-height: 100vh">
    <a-layout-header style="background: #001529; padding: 0 24px; display: flex; align-items: center">
      <div style="color: #fff; font-size: 18px; font-weight: bold">
        <ReadOutlined style="margin-right: 8px" />
        初中语文教师智能体
      </div>
    </a-layout-header>

    <a-layout-content style="background: #f0f2f5; padding: 24px">
      <router-view />
    </a-layout-content>
  </a-layout>
</template>

<script setup>
import { ReadOutlined } from '@ant-design/icons-vue'
</script>
