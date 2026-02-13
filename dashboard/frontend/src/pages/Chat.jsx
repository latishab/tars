import { useState, useEffect, useRef } from 'react'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Send, Trash2 } from 'lucide-react'

function Chat() {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [sending, setSending] = useState(false)
  const messagesEndRef = useRef(null)

  useEffect(() => {
    // Load chat history
    fetch('/api/chat/history?limit=50')
      .then(res => res.json())
      .then(data => {
        setMessages(data.messages || [])
      })
      .catch(console.error)
  }, [])

  useEffect(() => {
    // Scroll to bottom on new messages
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const sendMessage = async (e) => {
    e.preventDefault()
    if (!input.trim() || sending) return

    const userMessage = input.trim()
    setInput('')
    setSending(true)

    // Optimistically add user message
    const tempUserMsg = {
      role: 'user',
      text: userMessage,
      timestamp: new Date().toISOString(),
    }
    setMessages(prev => [...prev, tempUserMsg])

    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: userMessage }),
      })
      const data = await res.json()

      // Add assistant response
      setMessages(prev => [...prev, {
        role: 'assistant',
        text: data.response,
        timestamp: data.timestamp,
        actions: data.actions,
      }])
    } catch (err) {
      console.error('Send failed:', err)
      setMessages(prev => [...prev, {
        role: 'assistant',
        text: 'Error: Failed to send message',
        timestamp: new Date().toISOString(),
      }])
    }

    setSending(false)
  }

  const clearHistory = async () => {
    try {
      await fetch('/api/chat/history', { method: 'DELETE' })
      setMessages([])
    } catch (err) {
      console.error('Clear failed:', err)
    }
  }

  return (
    <div className="flex flex-col h-[calc(100vh-4rem)] p-4">
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-2xl font-bold text-foreground">Chat</h1>
        <Button variant="ghost" size="sm" onClick={clearHistory}>
          <Trash2 className="w-4 h-4" />
        </Button>
      </div>

      {/* Messages */}
      <Card className="flex-1 overflow-hidden">
        <CardContent className="p-4 h-full overflow-y-auto">
          {messages.length === 0 ? (
            <div className="h-full flex items-center justify-center text-muted-foreground">
              <p>Send a message to start chatting with TARS</p>
            </div>
          ) : (
            <div className="space-y-4">
              {messages.map((msg, i) => (
                <div
                  key={i}
                  className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`max-w-[80%] rounded-lg px-4 py-2 ${
                      msg.role === 'user'
                        ? 'bg-primary text-primary-foreground'
                        : 'bg-muted'
                    }`}
                  >
                    <p className="whitespace-pre-wrap">{msg.text}</p>
                    {msg.actions && msg.actions.length > 0 && (
                      <div className="mt-2 pt-2 border-t border-current/20">
                        <p className="text-xs opacity-70">
                          Actions: {msg.actions.join(', ')}
                        </p>
                      </div>
                    )}
                    <p className="text-xs opacity-50 mt-1">
                      {new Date(msg.timestamp).toLocaleTimeString()}
                    </p>
                  </div>
                </div>
              ))}
              <div ref={messagesEndRef} />
            </div>
          )}
        </CardContent>
      </Card>

      {/* Input */}
      <form onSubmit={sendMessage} className="mt-4 flex gap-2">
        <Input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Type a message..."
          disabled={sending}
          className="flex-1"
        />
        <Button type="submit" disabled={!input.trim() || sending}>
          <Send className="w-4 h-4" />
        </Button>
      </form>
    </div>
  )
}

export default Chat
