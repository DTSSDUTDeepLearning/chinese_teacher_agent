<template>
  <div class="home-container">
    <!-- 左侧对话列表 -->
    <div class="sidebar">
      <div class="sidebar-header">
        <a-button type="primary" block @click="createNewChat">
          <PlusOutlined />
          新建对话
        </a-button>
      </div>
      <div class="conversation-list">
        <div
          v-for="conv in conversations"
          :key="conv.id"
          class="conversation-item"
          :class="{ active: activeId === conv.id }"
          @click="selectConversation(conv.id)"
        >
          <MessageOutlined class="conv-icon" />
          <div class="conv-info">
            <div class="conv-title">{{ conv.title }}</div>
            <div class="conv-time">{{ conv.time }}</div>
          </div>
        </div>
      </div>
    </div>

    <!-- 右侧对话窗口 -->
    <div class="chat-area">
      <div class="messages" ref="messagesRef">
        <template v-if="activeConversation">
          <div
            v-for="(msg, index) in activeConversation.messages"
            :key="index"
            class="message"
            :class="msg.role"
          >
            <div class="avatar">
              <UserOutlined v-if="msg.role === 'user'" />
              <RobotOutlined v-else />
            </div>
            <div class="bubble">
              <div class="content">{{ msg.content }}</div>
              <div class="time">{{ msg.time }}</div>
            </div>
          </div>
          <!-- 思考中提示 -->
          <div v-if="isLoading" class="message assistant">
            <div class="avatar">
              <RobotOutlined />
            </div>
            <div class="bubble">
              <div class="content">
                <LoadingOutlined style="margin-right: 6px" />
                正在思考中...
              </div>
            </div>
          </div>
        </template>
        <div v-else class="empty-state">
          <RobotOutlined style="font-size: 48px; color: #bfbfbf" />
          <p style="color: #8c8c8c; margin-top: 16px">
            新建一个对话，或选择左侧历史对话
          </p>
        </div>
      </div>

      <div class="input-area">
        <a-textarea
          v-model:value="inputText"
          :rows="3"
          placeholder="输入您的问题..."
          :disabled="isLoading"
          @keydown.enter.prevent="sendMessage"
        />
        <a-button
          type="primary"
          :disabled="!inputText.trim() || isLoading"
          :loading="isLoading"
          @click="sendMessage"
        >
          <SendOutlined />
        </a-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, nextTick, onMounted } from 'vue'
import {
  PlusOutlined,
  MessageOutlined,
  UserOutlined,
  RobotOutlined,
  SendOutlined,
  LoadingOutlined,
} from '@ant-design/icons-vue'

// 对话列表从后端获取
const conversations = ref([])
const activeId = ref(null)
const inputText = ref('')
const messagesRef = ref(null)
const isLoading = ref(false)
const errorMsg = ref('')

const activeConversation = computed(() =>
  conversations.value.find((c) => String(c.id) === String(activeId.value))
)

function formatTime(dateStr) {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  return d.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}

function formatDate(dateStr) {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  const now = new Date()
  const isToday = d.toDateString() === now.toDateString()
  if (isToday) {
    return '今天 ' + formatTime(dateStr)
  }
  const yesterday = new Date(now)
  yesterday.setDate(yesterday.getDate() - 1)
  if (d.toDateString() === yesterday.toDateString()) {
    return '昨天 ' + formatTime(dateStr)
  }
  return d.toLocaleDateString('zh-CN')
}

async function fetchConversations() {
  try {
    const res = await fetch('/api/v1/conversations')
    if (!res.ok) throw new Error('获取对话列表失败')
    const data = await res.json()
    // 列表API只返回对话信息，不返回消息
    conversations.value = data.map((c) => ({
      id: c.id,
      title: c.title,
      time: formatDate(c.modify_time || c.create_time),
      messages: [], // 消息在选中对话时再加载
    }))
    // 默认选中第一个
    if (conversations.value.length > 0 && !activeId.value) {
      activeId.value = conversations.value[0].id
      await loadConversationMessages(conversations.value[0].id)
    }
  } catch (err) {
    console.error('fetchConversations error:', err)
  }
}

async function loadConversationMessages(conversationId) {
  try {
    const res = await fetch(`/api/v1/conversations/${conversationId}`)
    if (!res.ok) throw new Error('获取对话详情失败')
    const data = await res.json()
    const conv = conversations.value.find((c) => c.id === conversationId)
    if (conv) {
      conv.messages = (data.messages || []).map((m) => ({
        role: m.role,
        content: m.content,
        time: formatTime(m.create_time),
      }))
    }
  } catch (err) {
    console.error('loadConversationMessages error:', err)
  }
}

onMounted(() => {
  fetchConversations()
})

async function selectConversation(id) {
  activeId.value = id
  const conv = conversations.value.find((c) => c.id === id)
  if (conv && conv.messages.length === 0) {
    await loadConversationMessages(id)
  }
}

async function createNewChat() {
  try {
    const res = await fetch('/api/v1/conversations', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title: '新对话' }),
    })
    if (!res.ok) throw new Error('创建对话失败')
    const conv = await res.json()
    const newConv = {
      id: conv.id,
      title: conv.title,
      time: '刚刚',
      messages: [],
    }
    conversations.value.unshift(newConv)
    activeId.value = conv.id
  } catch (err) {
    console.error('createNewChat error:', err)
    alert('创建对话失败，请稍后重试')
  }
}

function nowTime() {
  return new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}

async function sendMessage() {
  const text = inputText.value.trim()
  if (!text || isLoading.value) return

  // 如果没有活跃对话，先创建一个
  let currentConv = activeConversation.value
  if (!currentConv) {
    await createNewChat()
    currentConv = activeConversation.value
    if (!currentConv) return
  }

  // 1. 添加用户消息
  currentConv.messages.push({
    role: 'user',
    content: text,
    time: nowTime(),
  })
  inputText.value = ''
  isLoading.value = true
  errorMsg.value = ''

  nextTick(() => {
    messagesRef.value.scrollTop = messagesRef.value.scrollHeight
  })

  try {
    // 2. 调用后端 /api/v1/chat
    const apiMessages = currentConv.messages.map((m) => ({
      role: m.role,
      content: m.content,
    }))

    console.log('Sending request to:', '/api/v1/chat')
    console.log('Request body:', JSON.stringify({ messages: apiMessages, conversation_id: currentConv.id }))

    const res = await fetch('/api/v1/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ messages: apiMessages, conversation_id: currentConv.id }),
    })

    if (!res.ok) {
      const errorText = await res.text()
      console.error('Backend error response:', errorText)
      alert(`后端错误 (${res.status}):\n${errorText}`)
      throw new Error(`HTTP ${res.status}: ${errorText}`)
    }

    const data = await res.json()

    // 3. 添加 AI 回复
    currentConv.messages.push({
      role: 'assistant',
      content: data.content,
      time: nowTime(),
    })

    // 更新标题（如果是默认标题，用第一条用户消息前20字作为标题）
    if (currentConv.title === '新对话') {
      currentConv.title = text.slice(0, 20)
    }
  } catch (err) {
    errorMsg.value = err.message
    currentConv.messages.push({
      role: 'assistant',
      content: `抱歉，请求出错：${err.message}，请稍后重试。`,
      time: nowTime(),
    })
  } finally {
    isLoading.value = false
    nextTick(() => {
      messagesRef.value.scrollTop = messagesRef.value.scrollHeight
    })
  }
}
</script>

<style scoped>
.home-container {
  display: flex;
  height: calc(100vh - 112px);
  background: #fff;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.sidebar {
  width: 280px;
  border-right: 1px solid #f0f0f0;
  display: flex;
  flex-direction: column;
  background: #fafafa;
}

.sidebar-header {
  padding: 16px;
  border-bottom: 1px solid #f0f0f0;
}

.conversation-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.conversation-item {
  display: flex;
  align-items: center;
  padding: 12px;
  border-radius: 6px;
  cursor: pointer;
  transition: background 0.2s;
  margin-bottom: 4px;
}

.conversation-item:hover {
  background: #f0f0f0;
}

.conversation-item.active {
  background: #e6f7ff;
}

.conv-icon {
  font-size: 20px;
  color: #8c8c8c;
  margin-right: 12px;
}

.conv-info {
  flex: 1;
  min-width: 0;
}

.conv-title {
  font-size: 14px;
  color: #262626;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.conv-time {
  font-size: 12px;
  color: #8c8c8c;
  margin-top: 2px;
}

.chat-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: #fff;
}

.messages {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
}

.message {
  display: flex;
  margin-bottom: 20px;
  align-items: flex-start;
}

.message.user {
  flex-direction: row-reverse;
}

.avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: #f0f0f0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  color: #595959;
  flex-shrink: 0;
  margin: 0 12px;
}

.bubble {
  max-width: 70%;
  padding: 12px 16px;
  border-radius: 12px;
  background: #f6ffed;
}

.message.assistant .bubble {
  background: #f0f5ff;
}

.content {
  font-size: 14px;
  line-height: 1.6;
  color: #262626;
  white-space: pre-wrap;
}

.time {
  font-size: 12px;
  color: #8c8c8c;
  margin-top: 4px;
  text-align: right;
}

.input-area {
  border-top: 1px solid #f0f0f0;
  padding: 16px 24px;
  display: flex;
  gap: 12px;
  align-items: flex-end;
}

.input-area :deep(.ant-input) {
  border-radius: 8px;
}
</style>
