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
import { ref, computed, nextTick } from 'vue'
import {
  PlusOutlined,
  MessageOutlined,
  UserOutlined,
  RobotOutlined,
  SendOutlined,
  LoadingOutlined,
} from '@ant-design/icons-vue'

const conversations = ref([
  {
    id: '1',
    title: '古诗文默写 - 七年级上册',
    time: '今天 14:30',
    messages: [
      {
        role: 'user',
        content: '帮我出10道七年级上册的古诗文默写题，体裁不限，仅重点篇目',
        time: '14:30',
      },
      {
        role: 'assistant',
        content:
          '好的，以下是为您生成的10道古诗文默写题：\n\n1. ______，志在千里。（《龟虽寿》曹操）\n2. 日月之行，______；星汉灿烂，______。（《观沧海》曹操）\n...',
        time: '14:31',
      },
    ],
  },
  {
    id: '2',
    title: '《岳阳楼记》知识图谱',
    time: '昨天 10:15',
    messages: [
      { role: 'user', content: '查看《岳阳楼记》的知识图谱', time: '10:15' },
      {
        role: 'assistant',
        content:
          '已为您生成《岳阳楼记》的知识图谱。中心节点为《岳阳楼记》，关联节点包括：作者范仲淹、朝代北宋、同作者作品《渔家傲·秋思》等。',
        time: '10:16',
      },
    ],
  },
])

const activeId = ref('1')
const inputText = ref('')
const messagesRef = ref(null)
const isLoading = ref(false)
const errorMsg = ref('')

const activeConversation = computed(() =>
  conversations.value.find((c) => c.id === activeId.value)
)

function selectConversation(id) {
  activeId.value = id
}

function createNewChat() {
  const newId = String(Date.now())
  conversations.value.unshift({
    id: newId,
    title: '新对话',
    time: '刚刚',
    messages: [],
  })
  activeId.value = newId
}

function nowTime() {
  return new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}

async function sendMessage() {
  const text = inputText.value.trim()
  if (!text || !activeConversation.value || isLoading.value) return

  // 1. 添加用户消息
  activeConversation.value.messages.push({
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
    const apiMessages = activeConversation.value.messages.map((m) => ({
      role: m.role,
      content: m.content,
    }))

    console.log('Sending request to:', '/api/v1/chat')
    console.log('Request body:', JSON.stringify({ messages: apiMessages }))

    const res = await fetch('/api/v1/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ messages: apiMessages }),
    })

    if (!res.ok) {
      const errorText = await res.text()
      console.error('Backend error response:', errorText)
      alert(`后端错误 (${res.status}):\n${errorText}`)
      throw new Error(`HTTP ${res.status}: ${errorText}`)
    }

    const data = await res.json()

    // 3. 添加 AI 回复
    activeConversation.value.messages.push({
      role: 'assistant',
      content: data.content,
      time: nowTime(),
    })
  } catch (err) {
    errorMsg.value = err.message
    activeConversation.value.messages.push({
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
