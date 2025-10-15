import React, { useState, useRef, useEffect } from 'react'
import axios from 'axios'
import './App.css'

const API_URL = 'http://localhost:8000'

function App() {
  const [messages, setMessages] = useState([])
  const [inputMessage, setInputMessage] = useState('')
  const [userType, setUserType] = useState('student')
  const [loading, setLoading] = useState(false)
  const messagesEndRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const sendMessage = async () => {
    if (!inputMessage.trim() || loading) return

    const userMessage = {
      id: Date.now(),
      text: inputMessage,
      isUser: true,
      timestamp: new Date()
    }

    setMessages(prev => [...prev, userMessage])
    setInputMessage('')
    setLoading(true)

    try {
      const response = await axios.post(`${API_URL}/chat`, {
        message: inputMessage,
        user_type: userType
      })

      const botMessage = {
        id: Date.now() + 1,
        text: response.data.response,
        isUser: false,
        timestamp: new Date(),
        userType: userType
      }

      setMessages(prev => [...prev, botMessage])
    } catch (error) {
      console.error('Ошибка:', error)
      const errorMessage = {
        id: Date.now() + 1,
        text: 'Ошибка соединения с сервером',
        isUser: false,
        isError: true,
        timestamp: new Date()
      }
      setMessages(prev => [...prev, errorMessage])
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

  return (
    <div className="app">
      <div className="chat-container">
        {/* Header */}
        <div className="chat-header">
          <h1>💬 Telegram Style Simulator</h1>
          <select 
            value={userType} 
            onChange={(e) => setUserType(e.target.value)}
            className="style-selector"
          >
            <option value="student">🎓 Студент</option>
            <option value="professor">👨‍🏫 Профессор</option>
            <option value="friend">🤝 Друг</option>
            <option value="boss">💼 Начальник</option>
          </select>
        </div>

        {/* Messages */}
        <div className="messages-container">
          {messages.length === 0 ? (
            <div className="empty-state">
              <h3>Начните диалог!</h3>
              <p>Выберите стиль общения и напишите сообщение</p>
            </div>
          ) : (
            messages.map((message) => (
              <div
                key={message.id}
                className={`message ${message.isUser ? 'user-message' : 'bot-message'} ${message.isError ? 'error' : ''}`}
              >
                <div className="message-content">
                  {message.text}
                </div>
                <div className="message-time">
                  {message.timestamp.toLocaleTimeString()}
                  {!message.isUser && message.userType && (
                    <span className="message-type">({message.userType})</span>
                  )}
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

        {/* Input */}
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
              📨
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

export default App