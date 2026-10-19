import React, { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, Zap, Database, AlertCircle, Sparkles } from 'lucide-react';
import { askChatbot } from '../services/api';
import { ChatMessage } from '../types';

export const ChatView: React.FC = () => {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'welcome',
      sender: 'bot',
      text: 'Nam Mô A Di Đà Phật! Tôi là trợ lý ảo Chùa Linh Ứng Bãi Bụt. Bạn có thể hỏi tôi về lịch sử chùa, tượng Phật Bà Quan Thế Âm 67m, chính điện hoặc các thông tin tham quan.',
      timestamp: 'Vừa xong'
    }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  const handleSend = async (questionText?: string) => {
    const q = (questionText || input).trim();
    if (!q || loading) return;

    const userMsg: ChatMessage = {
      id: `user_${Date.now()}`,
      sender: 'user',
      text: q,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    setMessages((prev) => [...prev, userMsg]);
    setInput('');
    setLoading(true);

    try {
      const res = await askChatbot(q);

      const botMsg: ChatMessage = {
        id: `bot_${Date.now()}`,
        sender: 'bot',
        text: res.answer,
        from_cache: res.from_cache,
        in_scope: res.in_scope,
        sources: res.sources,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };

      setMessages((prev) => [...prev, botMsg]);
    } catch (err: any) {
      setMessages((prev) => [
        ...prev,
        {
          id: `err_${Date.now()}`,
          sender: 'bot',
          text: err.message || 'Hệ thống trợ lý ảo đang bận, vui lòng thử lại sau giây lát',
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const sampleQuestions = [
    'Tượng Phật Bà cao bao nhiêu mét?',
    'Chùa mở cửa lúc mấy giờ?',
    'Lịch sử hình thành Chùa Linh Ứng?',
    'Cách làm bánh pizza hải sản?' // Câu hỏi ngoài phạm vi để demo UC03 E2
  ];

  return (
    <div className="flex flex-col h-[calc(100vh-120px)] bg-slate-50">
      {/* Danh sách câu hỏi gợi ý nhanh */}
      <div className="bg-white border-b border-slate-100 p-2.5 overflow-x-auto flex space-x-2 shrink-0 scrollbar-none">
        <span className="text-[11px] font-semibold text-slate-400 self-center px-1 shrink-0">
          Gợi ý câu hỏi:
        </span>
        {sampleQuestions.map((q, idx) => (
          <button
            key={idx}
            onClick={() => handleSend(q)}
            className="text-xs bg-slate-100 hover:bg-amber-50 hover:text-amber-700 hover:border-amber-200 border border-transparent text-slate-700 px-3 py-1 rounded-full whitespace-nowrap transition active:scale-95"
          >
            {q}
          </button>
        ))}
      </div>

      {/* Vùng tin nhắn Chat */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((m) => (
          <div
            key={m.id}
            className={`flex items-start space-x-2.5 ${m.sender === 'user' ? 'flex-row-reverse space-x-reverse' : ''}`}
          >
            <div
              className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 text-white text-xs shadow-sm ${
                m.sender === 'user' ? 'bg-blue-600' : 'bg-amber-600'
              }`}
            >
              {m.sender === 'user' ? <User size={16} /> : <Bot size={16} />}
            </div>

            <div className={`max-w-[82%] rounded-2xl p-3.5 shadow-sm ${
              m.sender === 'user'
                ? 'bg-blue-600 text-white rounded-tr-none'
                : 'bg-white border border-slate-100 text-slate-800 rounded-tl-none'
            }`}>
              {/* Badge nguồn Cache / RAG */}
              {m.sender === 'bot' && (
                <div className="flex items-center space-x-2 mb-1.5">
                  {m.from_cache ? (
                    <span className="inline-flex items-center space-x-1 px-2 py-0.5 bg-emerald-100 text-emerald-800 font-bold text-[10px] rounded-full border border-emerald-200">
                      <Zap size={11} className="fill-emerald-600" />
                      <span>⚡ TỪ BỘ NHỚ ĐỆM (CACHE HIT)</span>
                    </span>
                  ) : (
                    <span className="inline-flex items-center space-x-1 px-2 py-0.5 bg-purple-100 text-purple-800 font-bold text-[10px] rounded-full border border-purple-200">
                      <Database size={11} />
                      <span>🧠 RAG KNOWLEDGE STORE</span>
                    </span>
                  )}

                  {m.in_scope === false && (
                    <span className="inline-flex items-center space-x-1 px-2 py-0.5 bg-amber-100 text-amber-800 font-bold text-[10px] rounded-full">
                      <AlertCircle size={11} />
                      <span>NGOÀI PHẠM VI</span>
                    </span>
                  )}
                </div>
              )}

              <p className="text-xs sm:text-sm leading-relaxed whitespace-pre-line">{m.text}</p>

              <span className={`block text-[10px] mt-1 text-right ${
                m.sender === 'user' ? 'text-blue-100' : 'text-slate-400'
              }`}>
                {m.timestamp}
              </span>
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex items-start space-x-2.5">
            <div className="w-8 h-8 rounded-full bg-amber-600 flex items-center justify-center text-white text-xs">
              <Bot size={16} />
            </div>
            <div className="bg-white border border-slate-100 rounded-2xl rounded-tl-none p-3.5 shadow-sm flex items-center space-x-2">
              <Sparkles size={16} className="text-amber-600 animate-spin" />
              <span className="text-xs text-slate-500">Trợ lý ảo đang tra cứu tri thức...</span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Khung nhập tin nhắn */}
      <div className="p-3 bg-white border-t border-slate-100">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSend();
          }}
          className="flex items-center space-x-2"
        >
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Hỏi trợ lý ảo về Chùa Linh Ứng..."
            className="flex-1 bg-slate-50 border border-slate-200 rounded-2xl px-4 py-2.5 text-xs sm:text-sm focus:outline-none focus:ring-2 focus:ring-amber-500 focus:bg-white transition"
          />
          <button
            type="submit"
            disabled={!input.trim() || loading}
            className="p-2.5 bg-amber-600 hover:bg-amber-700 active:scale-95 text-white rounded-2xl transition disabled:opacity-40 shadow-sm"
          >
            <Send size={18} />
          </button>
        </form>
      </div>
    </div>
  );
};
