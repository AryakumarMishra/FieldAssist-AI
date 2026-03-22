import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { Send, MessageSquare, Plus } from 'lucide-react';
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

  // Initial load
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

    try {
      // Create session if it's the first message
      if (!currentSessionId) {
        // Title can be the first few words of the query
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

      // Send to LLM
      const res = await axios.post(`${API_BASE}/chat`, {
        query: query,
        category: category,
        session_id: currentSessionId
      });

      const assistantMsg = {
        id: Date.now() + 1,
        role: 'assistant',
        content: res.data.answer,
        source_documents: res.data.source_documents
      };

      setMessages(prev => [...prev, assistantMsg]);
    } catch (err) {
      console.error('Chat error:', err);
      // Let the user know the backend couldn't be reached
      setMessages(prev => [...prev, { id: Date.now(), role: 'assistant', content: 'An error occurred while connecting to the backend. Ensure FastAPI is running on port 8000.' }]);
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
            <button 
              key={s.id} 
              className={`chat-item ${activeSession?.id === s.id ? 'active' : ''}`}
              onClick={() => loadSession(s)}
            >
              <span className="chat-title"><MessageSquare size={14} style={{marginRight: '6px', verticalAlign: 'middle'}}/> {s.title || 'Untitled'}</span>
              <span className="chat-category">{s.category.replace('_', ' ')}</span>
            </button>
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
