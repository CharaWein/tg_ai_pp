import React, { useState, useRef, useEffect } from 'react'
import './App.css'

function App() {
  const [chats, setChats] = useState([
    {
      id: 1,
      name: 'Первая беседа',
      messages: [],
      createdAt: new Date()
    }
  ])
  const [activeChatId, setActiveChatId] = useState(1)
  const [inputMessage, setInputMessage] = useState('')
  const [loading, setLoading] = useState(false)
  const [editingChatId, setEditingChatId] = useState(null)
  const [editChatName, setEditChatName] = useState('')
  const messagesEndRef = useRef(null)

  // Получение активного чата
  const activeChat = chats.find(chat => chat.id === activeChatId)

  // Демо-ответы AI
  const demoResponses = [
    "Привет! Как дела?",
    "Интересно, расскажи подробнее!",
    "Я понимаю о чем ты...",
    "Давай обсудим это детальнее?",
    "Хм, никогда об этом не задумывался!",
    "Это действительно важно!",
    "Продолжайте, я вас слушаю!",
    "Как интересно! А что было дальше?",
    "Я бы поступил точно так же!",
    "Отличная мысль, поддерживаю!"
  ]

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  useEffect(() => {
    scrollToBottom()
  }, [activeChat?.messages])

  const getRandomResponse = () => {
    return demoResponses[Math.floor(Math.random() * demoResponses.length)]
  }

  const sendMessage = async () => {
  if (!inputMessage.trim() || loading) return

  // Сообщение пользователя
  const userMessage = {
    id: Date.now(),
    text: inputMessage,
    isUser: true,
    timestamp: new Date()
  }

  // Обновляем сообщения в активном чате
  const updatedChats = chats.map(chat => 
    chat.id === activeChatId 
      ? { ...chat, messages: [...chat.messages, userMessage] }
      : chat
  )
  setChats(updatedChats)
  setInputMessage('')
  setLoading(true)

  try {
    // Реальный вызов к бэкенду
    const response = await fetch('/api/clone/YOUR_TOKEN/chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ message: inputMessage })
    })

    if (response.ok) {
      const data = await response.json()
      
      const botMessage = {
        id: Date.now() + 1,
        text: data.response,
        isUser: false,
        timestamp: new Date()
      }

      const finalChats = updatedChats.map(chat => 
        chat.id === activeChatId 
          ? { ...chat, messages: [...chat.messages, botMessage] }
          : chat
      )
      setChats(finalChats)
    } else {
      throw new Error('Ошибка сервера')
    }
  } catch (error) {
    console.error('Ошибка:', error)
    // Запасной демо-ответ при ошибке
    const botMessage = {
      id: Date.now() + 1,
      text: "Извините, произошла ошибка соединения",
      isUser: false,
      timestamp: new Date()
    }
    
    const finalChats = updatedChats.map(chat => 
      chat.id === activeChatId 
        ? { ...chat, messages: [...chat.messages, botMessage] }
        : chat
    )
    setChats(finalChats)
  } finally {
    setLoading(false)
  }
}

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  // Создание нового чата
  const createNewChat = () => {
    const newChatId = Date.now()
    const newChat = {
      id: newChatId,
      name: `Беседа ${chats.length + 1}`,
      messages: [],
      createdAt: new Date()
    }
    setChats([...chats, newChat])
    setActiveChatId(newChatId)
  }

  // Удаление чата
  const deleteChat = (chatId, e) => {
    e.stopPropagation()
    if (chats.length === 1) {
      alert('Нельзя удалить последний чат')
      return
    }
    
    const filteredChats = chats.filter(chat => chat.id !== chatId)
    setChats(filteredChats)
    
    // Если удаляем активный чат, переключаемся на первый доступный
    if (chatId === activeChatId) {
      setActiveChatId(filteredChats[0].id)
    }
  }

  // Начало редактирования названия чата
  const startEditingChat = (chatId, chatName, e) => {
    e.stopPropagation()
    setEditingChatId(chatId)
    setEditChatName(chatName)
  }

  // Сохранение нового названия чата
  const saveChatName = (chatId, e) => {
    e?.stopPropagation()
    if (editChatName.trim()) {
      const updatedChats = chats.map(chat =>
        chat.id === chatId
          ? { ...chat, name: editChatName.trim() }
          : chat
      )
      setChats(updatedChats)
    }
    setEditingChatId(null)
    setEditChatName('')
  }

  // Отмена редактирования
  const cancelEditing = (e) => {
    e?.stopPropagation()
    setEditingChatId(null)
    setEditChatName('')
  }

  // Обработка нажатия Enter при редактировании
  const handleEditKeyPress = (chatId, e) => {
    if (e.key === 'Enter') {
      saveChatName(chatId, e)
    } else if (e.key === 'Escape') {
      cancelEditing(e)
    }
  }

  // Форматирование времени для превью чата
  const formatTime = (date) => {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  }

  // Получение последнего сообщения для превью
  const getLastMessagePreview = (messages) => {
    if (messages.length === 0) return 'Нет сообщений'
    const lastMessage = messages[messages.length - 1]
    const text = lastMessage.text.length > 30 
      ? lastMessage.text.substring(0, 30) + '...' 
      : lastMessage.text
    return `${lastMessage.isUser ? 'Вы: ' : 'AI: '}${text}`
  }

  return (
    <div className="app">
      <div className="app-container">
        {/* Боковая панель с чатами */}
        <div className="sidebar">
          <div className="sidebar-header">
            <h2>Чаты</h2>
            <button onClick={createNewChat} className="new-chat-btn">
              + Новый чат
            </button>
          </div>
          
          <div className="chats-list">
            {chats.map(chat => (
              <div
                key={chat.id}
                className={`chat-preview ${chat.id === activeChatId ? 'active' : ''}`}
                onClick={() => setActiveChatId(chat.id)}
              >
                <div className="chat-preview-content">
                  <div className="chat-header-row">
                    <button 
                      onClick={(e) => startEditingChat(chat.id, chat.name, e)}
                      className="edit-chat-btn"
                      title="Переименовать чат"
                    >
                      ✎
                    </button>
                    
                    {editingChatId === chat.id ? (
                      <div className="chat-name-editing">
                        <input
                          type="text"
                          value={editChatName}
                          onChange={(e) => setEditChatName(e.target.value)}
                          onKeyPress={(e) => handleEditKeyPress(chat.id, e)}
                          onClick={(e) => e.stopPropagation()}
                          className="chat-name-input"
                          autoFocus
                          maxLength={50}
                          placeholder="Название чата"
                        />
                      </div>
                    ) : (
                      <div className="chat-name">{chat.name}</div>
                    )}
                  </div>
                  
                  <div className="chat-last-message">
                    {getLastMessagePreview(chat.messages)}
                  </div>
                  <div className="chat-time">
                    {formatTime(chat.createdAt)}
                  </div>
                </div>
                
                <button 
                  onClick={(e) => deleteChat(chat.id, e)}
                  className="delete-chat-btn"
                  title="Удалить чат"
                >
                  ×
                </button>
              </div>
            ))}
          </div>
        </div>

        {/* Основная область чата */}
        <div className="main-content">
          <div className="chat-header">
            <h1>{activeChat?.name || 'Чат'}</h1>
            <div className="chat-info">
              {activeChat?.messages.length || 0} сообщений
            </div>
          </div>

          <div className="messages-container">
            {activeChat?.messages.length === 0 ? (
              <div className="empty-state">
                <div className="empty-icon">💬</div>
                <h3>Начните общение</h3>
                <p>Напишите сообщение, чтобы начать диалог с AI</p>
              </div>
            ) : (
              activeChat?.messages.map((message) => (
                <div
                  key={message.id}
                  className={`message ${message.isUser ? 'user-message' : 'bot-message'}`}
                >
                  <div className="message-content">
                    {message.text}
                  </div>
                  <div className="message-time">
                    {formatTime(message.timestamp)}
                  </div>
                </div>
              ))
            )}
            
            {loading && (
              <div className="message bot-message">
                <div className="message-content typing">
                  <div className="typing-dots">
                    <span></span>
                    <span></span>
                    <span></span>
                  </div>
                </div>
              </div>
            )}
            
            <div ref={messagesEndRef} />
          </div>

          <div className="input-container">
            <div className="input-wrapper">
              <input
                type="text"
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Введите сообщение..."
                disabled={loading}
                className="message-input"
              />
              <button 
                onClick={sendMessage}
                disabled={loading || !inputMessage.trim()}
                className="send-button"
              >
                {loading ? '⏳' : '➤'}
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Модальное окно редактирования */}
      {editingChatId && (
        <div className="modal-overlay" onClick={cancelEditing}>
          <div className="edit-modal" onClick={(e) => e.stopPropagation()}>
            <h3>Переименовать чат</h3>
            <input
              type="text"
              value={editChatName}
              onChange={(e) => setEditChatName(e.target.value)}
              onKeyPress={(e) => handleEditKeyPress(editingChatId, e)}
              className="modal-input"
              autoFocus
              maxLength={50}
              placeholder="Введите новое название"
            />
            <div className="modal-actions">
              <button 
                onClick={cancelEditing}
                className="modal-btn cancel"
              >
                Отмена
              </button>
              <button 
                onClick={() => saveChatName(editingChatId)}
                className="modal-btn save"
                disabled={!editChatName.trim()}
              >
                Сохранить
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default App