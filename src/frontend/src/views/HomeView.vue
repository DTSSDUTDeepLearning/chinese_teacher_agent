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
              <!-- 用户消息：纯文本 -->
              <div v-if="msg.role === 'user'" class="content">{{ msg.content }}</div>
              <!-- AI 消息：Markdown 渲染 -->
              <div v-else class="content markdown-body" v-html="renderMarkdown(msg.content)"></div>
              <div class="msg-footer">
                <span class="time">{{ msg.time }}</span>
                <a-button
                  v-if="msg.role === 'assistant'"
                  type="text"
                  size="small"
                  class="copy-btn"
                  @click="copyContent(msg.content)"
                >
                  <CopyOutlined />
                  复制
                </a-button>
              </div>
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
          <p style="color: #bfbfbf; margin-top: 8px; font-size: 13px">
            试试说："帮我出6道八年级下学期的古诗文默写题"
          </p>
        </div>
      </div>

      <div class="input-area">
        <a-textarea
          v-model:value="inputText"
          :rows="3"
          placeholder="输入您的问题，如：帮我出6道八年级下学期的古诗文默写题"
          :disabled="isLoading"
          @keydown="handleKeydown"
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
import { marked } from 'marked'
import {
  PlusOutlined,
  MessageOutlined,
  UserOutlined,
  RobotOutlined,
  SendOutlined,
  LoadingOutlined,
  CopyOutlined,
} from '@ant-design/icons-vue'
import { message as antMessage } from 'ant-design-vue'

// Markdown 渲染配置
marked.setOptions({
  breaks: true,
  gfm: true,
})

const conversations = ref([])
const activeId = ref(null)
const inputText = ref('')
const messagesRef = ref(null)
const isLoading = ref(false)
const errorMsg = ref('')

const activeConversation = computed(() =>
  conversations.value.find((c) => String(c.id) === String(activeId.value))
)

// 出题意图关键词
const QUIZ_KEYWORDS = ['默写', '出题', '填空', '理解性默写', '上下句', '古诗文', '古诗', '古文']
// quiz 追问特征（quiz_agent 范围不完整时的追问话术）
const QUIZ_FOLLOWUP_MARKERS = ['请问您需要哪个年级', '上册、下册，还是都要']

function isQuizRequest(text, messages) {
  // 1. 当前消息含出题关键词 -> 走 quiz
  if (QUIZ_KEYWORDS.some((kw) => text.includes(kw))) return true
  // 2. 当前消息不含关键词，但上一条 assistant 消息是 quiz 的追问 -> 仍走 quiz（多轮补充）
  if (messages && messages.length >= 1) {
    const lastAssistant = [...messages].reverse().find((m) => m.role === 'assistant')
    if (lastAssistant && QUIZ_FOLLOWUP_MARKERS.some((mk) => lastAssistant.content.includes(mk))) {
      return true
    }
  }
  return false
}

function renderMarkdown(text) {
  if (!text) return ''
  try {
    return marked.parse(text)
  } catch (e) {
    return text
  }
}

async function copyContent(content) {
  try {
    await navigator.clipboard.writeText(content)
    antMessage.success('已复制到剪贴板')
  } catch (e) {
    antMessage.error('复制失败，请手动选择文本复制')
  }
}

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
    conversations.value = data.map((c) => ({
      id: c.id,
      title: c.title,
      time: formatDate(c.modify_time || c.create_time),
      messages: [],
    }))
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
    antMessage.error('创建对话失败，请稍后重试')
  }
}

function nowTime() {
  return new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}

function handleKeydown(e) {
  // 中文输入法组合输入中，回车用于确认候选词，不发送
  if (e.isComposing || e.keyCode === 229) return
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    sendMessage()
  }
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
  // 清空输入框：先置空，并在下一轮事件循环再兜底一次，
  // 防止中文输入法 compositionend 在 keydown 之后把文本写回
  inputText.value = ''
  await nextTick()
  inputText.value = ''
  isLoading.value = true
  errorMsg.value = ''

  nextTick(() => {
    messagesRef.value.scrollTop = messagesRef.value.scrollHeight
  })

  try {
    let replyContent = ''

    // 2. 自动路由：出题意图走 /quiz/generate，其他走 /chat
    //    多轮追问场景：上一条 assistant 是 quiz 追问时，当前消息仍走 quiz
    if (isQuizRequest(text, currentConv.messages)) {
      console.log('路由到出题Agent：/api/v1/quiz/generate')
      // 构建对话历史（当前消息之前的历史），传给 quiz agent 合并解析
      const history = currentConv.messages.map((m) => ({
        role: m.role,
        content: m.content,
      }))
      const res = await fetch('/api/v1/quiz/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text, history }),
      })
      if (!res.ok) {
        const errorText = await res.text()
        throw new Error(`HTTP ${res.status}: ${errorText}`)
      }
      const data = await res.json()
      replyContent = data.content
    } else {
      console.log('路由到通用聊天：/api/v1/chat')
      const apiMessages = currentConv.messages.map((m) => ({
        role: m.role,
        content: m.content,
      }))
      const res = await fetch('/api/v1/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ messages: apiMessages, conversation_id: currentConv.id }),
      })
      if (!res.ok) {
        const errorText = await res.text()
        throw new Error(`HTTP ${res.status}: ${errorText}`)
      }
      const data = await res.json()
      replyContent = data.content
    }

    // 3. 添加 AI 回复
    currentConv.messages.push({
      role: 'assistant',
      content: replyContent,
      time: nowTime(),
    })

    // 更新标题
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

/* Markdown 渲染样式 */
.markdown-body {
  white-space: normal;
}

.markdown-body :deep(ol),
.markdown-body :deep(ul) {
  padding-left: 24px;
  margin: 8px 0;
}

.markdown-body :deep(li) {
  margin: 4px 0;
}

.markdown-body :deep(p) {
  margin: 8px 0;
}

.markdown-body :deep(strong) {
  font-weight: 600;
}

.msg-footer {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  margin-top: 4px;
  gap: 8px;
}

.time {
  font-size: 12px;
  color: #8c8c8c;
}

.copy-btn {
  font-size: 12px;
  color: #8c8c8c;
  padding: 0 4px;
  height: 24px;
}

.copy-btn:hover {
  color: #1677ff;
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
