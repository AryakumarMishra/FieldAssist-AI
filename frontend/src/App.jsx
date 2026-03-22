import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { Send, MessageSquare, Plus, Trash2 } from 'lucide-react';
import './index.css';

const API_BASE = 'http://localhost:8000'; // FastAPI configuration

function App() {
  const [sessions, setSessions] = useState([]);
  const [activeSession, setActiveSession] = useState(null);
  const [messages, setMessages] = useState([]);
  
  const [inputStr, setInputStr] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('bns_2023');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    fetchSessions();
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const fetchSessions = async () => {
    try {
      const res = await axios.get(`${API_BASE}/chats`);
      setSessions(res.data);
    } catch (err) {
      console.error('Failed to fetch sessions', err);
    }
  };

  const loadSession = async (session) => {
    setActiveSession(session);
    try {
      const res = await axios.get(`${API_BASE}/chats/${session.id}/messages`);
      // Parse historical source documents if we stored them (historically we didn't, but going forward we just store raw content)
      setMessages(res.data);
    } catch (err) {
      console.error('Failed to load messages', err);
    }
  };

  const startNewChat = () => {
    setActiveSession(null);
    setMessages([]);
    setInputStr('');
  };

  const handleDeleteSession = async (e, sessionId) => {
    e.stopPropagation(); // prevent triggering the chat load
    try {
      await axios.delete(`${API_BASE}/chats/${sessionId}`);
      setSessions(prev => prev.filter(s => s.id !== sessionId));
      if (activeSession?.id === sessionId) {
        startNewChat();
      }
    } catch (err) {
      console.error('Failed to delete chat:', err);
    }
  };

  const handleSend = async () => {
    if (!inputStr.trim()) return;
    const query = inputStr.trim();
    setInputStr('');
    
    // Optimistic UI for User Message
    const optimisticUserMsg = { id: Date.now(), role: 'user', content: query };
    setMessages(prev => [...prev, optimisticUserMsg]);
    setIsLoading(true);

    let currentSessionId = activeSession?.id;
    let category = activeSession ? activeSession.category : selectedCategory;

    // Create boundary for the streaming message
    const assistantId = Date.now() + 1;
    setMessages(prev => [...prev, { id: assistantId, role: 'assistant', content: '', source_documents: [] }]);

    try {
      // Create session if it's the first message
      if (!currentSessionId) {
        const title = query.length > 30 ? query.substring(0, 30) + '...' : query;
        const res = await axios.post(`${API_BASE}/chats`, {
          title: title,
          category: category
        });
        currentSessionId = res.data.session_id;
        const newSessionObj = { id: currentSessionId, title, category, created_at: new Date().toISOString() };
        setActiveSession(newSessionObj);
        setSessions(prev => [newSessionObj, ...prev]);
      }

      // Stream the LLM response using native Fetch API
      const response = await fetch(`${API_BASE}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: query,
          category: category,
          session_id: currentSessionId
        })
      });

      if (!response.body) throw new Error('ReadableStream not supported.');

      const reader = response.body.getReader();
      const decoder = new TextDecoder('utf-8');
      let done = false;
      let streamedText = "";

      // Remove the spinning loader as soon as the connection opens
      setIsLoading(false);

      while (!done) {
        const { value, done: doneReading } = await reader.read();
        done = doneReading;
        if (value) {
          const chunk = decoder.decode(value, { stream: true });
          streamedText += chunk;
          
          let displayContent = streamedText;
          let sources = [];
          
          // Detect sources boundary securely
          if (streamedText.includes('__SOURCES_JSON__')) {
            const parts = streamedText.split('__SOURCES_JSON__');
            displayContent = parts[0];
            const sourcesRaw = parts[1].split('__END_SOURCES__')[0];
            try {
              sources = JSON.parse(sourcesRaw);
            } catch (e) {}
          }

          setMessages(prev => prev.map(msg => 
            msg.id === assistantId ? { ...msg, content: displayContent, source_documents: sources } : msg
          ));
        }
      }

    } catch (err) {
      console.error('Chat error:', err);
      setMessages(prev => prev.map(msg => 
        msg.id === assistantId ? { ...msg, content: 'An error occurred while connecting to the backend.' } : msg
      ));
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="app-container">
      {/* Sidebar */}
      <aside className="sidebar">
        <div className="sidebar-header">
          <button className="new-chat-btn" onClick={startNewChat}>
            <Plus size={18} /> New Session
          </button>
        </div>
        <div className="chat-list">
          {sessions.map(s => (
            <div 
              key={s.id} 
              className={`chat-item ${activeSession?.id === s.id ? 'active' : ''}`}
              onClick={() => loadSession(s)}
              style={{flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between'}}
            >
              <div style={{display: 'flex', flexDirection: 'column', gap: '4px', overflow: 'hidden'}}>
                <span className="chat-title"><MessageSquare size={14} style={{marginRight: '6px', verticalAlign: 'middle'}}/> {s.title || 'Untitled'}</span>
                <span className="chat-category">{s.category.replace('_', ' ')}</span>
              </div>
              <button 
                onClick={(e) => handleDeleteSession(e, s.id)}
                style={{background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', padding: '4px'}}
                title="Delete Chat"
              >
                <Trash2 size={16} />
              </button>
            </div>
          ))}
        </div>
      </aside>

      {/* Main Area */}
      <main className="main-area">
        <header className="top-bar">
          {!activeSession ? (
            <select 
              className="category-select" 
              value={selectedCategory} 
              onChange={e => setSelectedCategory(e.target.value)}
            >
              <option value="bns_2023">BNS 2023</option>
              <option value="military_law">Military Law</option>
              <option value="tccc_guide">TCCC Guide</option>
            </select>
          ) : (
            <div style={{color: 'var(--text-muted)'}}>
              Active Context: <strong style={{color: '#fff'}}>{activeSession.category.toUpperCase().replace('_', ' ')}</strong>
            </div>
          )}
        </header>

        <div className="messages-container">
          {messages.length === 0 ? (
            <div className="empty-state">
              <h2>FieldAssist AI</h2>
              <p>Highly Secure Offline Legal & Procedural Guide</p>
              <p style={{marginTop: '12px', fontSize: '0.9rem'}}>Select a context category and begin querying.</p>
            </div>
          ) : (
            messages.map((msg, idx) => (
              <div key={idx} className={`message-wrapper ${msg.role}`}>
                <div className="message-bubble">
                  {msg.content}
                </div>
                {msg.source_documents && msg.source_documents.length > 0 && (
                  <div className="source-docs">
                    <span style={{color: 'var(--text-muted)', fontSize: '0.8rem', marginTop: '4px'}}>Sourced Context:</span>
                    {msg.source_documents.map((doc, i) => (
                      <div key={i} className="source-doc">"{doc.substring(0, 200)}..."</div>
                    ))}
                  </div>
                )}
              </div>
            ))
          )}
          {isLoading && (
            <div className="message-wrapper assistant">
              <div className="loading-dots">
                <span></span><span></span><span></span>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        <div className="input-area">
          <div className="input-container">
            <textarea 
              className="chat-input"
              placeholder="Query FieldAssist..."
              value={inputStr}
              onChange={e => setInputStr(e.target.value)}
              onKeyDown={e => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleSend();
                }
              }}
            />
            <button 
              className="send-btn" 
              onClick={handleSend}
              disabled={isLoading || !inputStr.trim()}
            >
              <Send size={20} />
            </button>
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;
