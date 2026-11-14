import { useState, useEffect, useRef } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { chatbotClient } from '../api/client';
import { ChatMessage, ChatSource } from '../types';
import { 
  ArrowLeft, 
  Send, 
  Bot, 
  User, 
  Sparkles, 
  AlertCircle, 
  MapPin, 
  HelpCircle,
  Clock
} from 'lucide-react';

const SUGGESTIONS_BY_LANG: Record<string, string[]> = {
  vi: [
    'Chùa Linh Ứng mở cửa vào những khung giờ nào?',
    'Tượng Phật Bà Quan Âm cao bao nhiêu mét?',
    'Đi viếng chùa cần lưu ý trang phục như thế nào?',
    'Chùa Linh Ứng được khởi công xây dựng năm nào?'
  ],
  en: [
    'What are the opening hours of Linh Ung Pagoda?',
    'How tall is the Lady Buddha Statue?',
    'What is the dress code for visiting the pagoda?',
    'Tell me the history of Linh Ung Pagoda.'
  ],
  zh: [
    '灵应寺的开放时间是几点？',
    '观音佛像有多高？',
    '参观寺庙需要注意什么着装礼仪？'
  ]
};

const WELCOME_MESSAGES: Record<string, string> = {
  vi: 'Kính chào quý khách! Tôi là trợ lý ảo AI hướng dẫn viên của Chùa Linh Ứng Bãi Bụt. Quý khách cần tìm hiểu thông tin gì về chùa, lịch sử các pho tượng hay quy định tham quan?',
  en: 'Welcome! I am your AI tour guide assistant for Linh Ung Pagoda. How can I help you explore the temple, statues, and visitor guidelines today?',
  zh: '欢迎光临！我是岘港灵应寺的AI虚拟导游助手。今天有什么我可以帮您的吗？'
};

export default function ChatbotPage() {
  const navigate = useNavigate();
  const location = useLocation();

  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputText, setInputText] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string>('');
  const [currentLang, setCurrentLang] = useState<string>('vi');

  const messagesEndRef = useRef<HTMLDivElement | null>(null);

  // Cuộn xuống tin nhắn mới nhất
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  useEffect(() => {
    const lang = localStorage.getItem('customer_lang') || 'vi';
    setCurrentLang(lang);

    // Khởi tạo tin nhắn chào mừng
    const welcomeText = WELCOME_MESSAGES[lang] || WELCOME_MESSAGES.en;
    const initialMsg: ChatMessage = {
      id: 'welcome',
      sender: 'bot',
      text: welcomeText,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };
    setMessages([initialMsg]);

    // Kiểm tra câu hỏi được chuyển từ POI Detail
    const prefilled = (location.state as any)?.prefilledQuestion;
    if (prefilled) {
      handleSendMessage(prefilled, lang);
    }
  }, [location.state]);

  const handleSendMessage = async (textToSend?: string, langOverride?: string) => {
    const question = (textToSend || inputText).trim();
    if (!question || loading) return;

    const lang = langOverride || currentLang;
    const timeStr = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

    // 1. Thêm tin nhắn của User
    const userMsg: ChatMessage = {
      id: `u_${Date.now()}`,
      sender: 'user',
      text: question,
      timestamp: timeStr
    };
    setMessages((prev) => [...prev, userMsg]);
    setInputText('');
    setErrorMsg('');
    setLoading(true);

    try {
      // 2. Gửi API Chatbot Ask
      const response = await chatbotClient.post('/api/chatbot/ask', {
        question,
        lang
      });

      if (response.data) {
        const botMsg: ChatMessage = {
          id: `b_${Date.now()}`,
          sender: 'bot',
          text: response.data.answer,
          sources: response.data.sources || [],
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        };
        setMessages((prev) => [...prev, botMsg]);
      }
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      let errText = 'Đã có lỗi xảy ra khi kết nối tới Trợ lý ảo AI. Vui lòng thử lại.';
      if (typeof detail === 'object' && detail?.error_code === 'CHAT_RATE_LIMIT') {
        errText = detail.message || 'Bạn đã đạt giới hạn câu hỏi trong phiên tham quan này.';
      } else if (typeof detail === 'string') {
        errText = detail;
      }
      setErrorMsg(errText);
    } finally {
      setLoading(false);
    }
  };

  const suggestions = SUGGESTIONS_BY_LANG[currentLang] || SUGGESTIONS_BY_LANG.vi;

  return (
    <div className="flex-1 flex flex-col h-screen bg-stone-100 overflow-hidden">
      {/* Header */}
      <header className="px-4 py-3 bg-amber-600 text-white flex items-center justify-between shadow-md shrink-0 z-10">
        <div className="flex items-center gap-3">
          <button
            onClick={() => navigate('/map')}
            className="p-1.5 rounded-full hover:bg-amber-700 text-white transition-colors"
            title="Quay lại bản đồ"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div>
            <div className="flex items-center gap-1.5">
              <h1 className="text-sm font-bold tracking-tight">HƯỚNG DẪN VIÊN AI</h1>
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            </div>
            <p className="text-[11px] text-amber-100">Chùa Linh Ứng Bãi Bụt • Trợ lý 24/7</p>
          </div>
        </div>

        <div className="p-2 rounded-full bg-amber-700/60 text-amber-200">
          <Sparkles className="w-4 h-4 text-amber-300" />
        </div>
      </header>

      {/* Vùng Tin nhắn Chat */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((msg) => {
          const isUser = msg.sender === 'user';
          return (
            <div
              key={msg.id}
              className={`flex gap-2.5 max-w-[88%] ${isUser ? 'ml-auto flex-row-reverse' : 'mr-auto'}`}
            >
              {/* Avatar Icon */}
              <div
                className={`w-7 h-7 rounded-full flex items-center justify-center shrink-0 text-white shadow-sm ${
                  isUser ? 'bg-amber-700' : 'bg-amber-600'
                }`}
              >
                {isUser ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
              </div>

              {/* Message Bubble */}
              <div>
                <div
                  className={`p-3.5 rounded-2xl text-xs sm:text-sm leading-relaxed shadow-sm ${
                    isUser
                      ? 'bg-amber-600 text-white rounded-tr-none'
                      : 'bg-white text-stone-800 border border-stone-200/80 rounded-tl-none whitespace-pre-line'
                  }`}
                >
                  {msg.text}
                </div>

                {/* Danh sách nguồn tham khảo (Sources) */}
                {!isUser && msg.sources && msg.sources.length > 0 && (
                  <div className="mt-2 space-y-1">
                    <span className="text-[10px] font-semibold text-stone-400 uppercase tracking-wider block">
                      Tham khảo cẩm nang:
                    </span>
                    <div className="flex flex-wrap gap-1.5">
                      {msg.sources.map((src: ChatSource) => (
                        <button
                          key={src.poi_id}
                          onClick={() => navigate(`/poi/${src.poi_id}`)}
                          className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-amber-50 hover:bg-amber-100 border border-amber-200 text-amber-900 text-[11px] font-medium transition-colors"
                        >
                          <MapPin className="w-3 h-3 text-amber-600" />
                          <span>{src.title}</span>
                        </button>
                      ))}
                    </div>
                  </div>
                )}

                <div className={`text-[10px] text-stone-400 mt-1 flex items-center gap-1 ${isUser ? 'justify-end' : ''}`}>
                  <Clock className="w-2.5 h-2.5" />
                  <span>{msg.timestamp}</span>
                </div>
              </div>
            </div>
          );
        })}

        {/* Loading Indicator */}
        {loading && (
          <div className="flex gap-2.5 max-w-[85%] mr-auto">
            <div className="w-7 h-7 rounded-full bg-amber-600 flex items-center justify-center shrink-0 text-white shadow-sm">
              <Bot className="w-4 h-4" />
            </div>
            <div className="p-3.5 rounded-2xl rounded-tl-none bg-white border border-stone-200 text-stone-500 text-xs flex items-center gap-2">
              <div className="flex gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-amber-600 animate-bounce" style={{ animationDelay: '0ms' }} />
                <span className="w-1.5 h-1.5 rounded-full bg-amber-600 animate-bounce" style={{ animationDelay: '150ms' }} />
                <span className="w-1.5 h-1.5 rounded-full bg-amber-600 animate-bounce" style={{ animationDelay: '300ms' }} />
              </div>
              <span>Trợ lý AI đang tra cứu cẩm nang...</span>
            </div>
          </div>
        )}

        {/* Lỗi cảnh báo */}
        {errorMsg && (
          <div className="p-3 rounded-xl bg-red-50 border border-red-200 text-red-700 text-xs flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-red-500 shrink-0" />
            <span>{errorMsg}</span>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Gợi ý câu hỏi nhanh (Quick suggestions) */}
      {messages.length <= 2 && (
        <div className="px-4 py-2 bg-stone-50 border-t border-stone-200/80 shrink-0">
          <div className="flex items-center gap-1.5 text-[11px] font-semibold text-stone-500 mb-1.5">
            <HelpCircle className="w-3.5 h-3.5 text-amber-600" />
            <span>Câu hỏi thường gặp:</span>
          </div>
          <div className="flex gap-2 overflow-x-auto pb-1 no-scrollbar">
            {suggestions.map((sug, idx) => (
              <button
                key={idx}
                onClick={() => handleSendMessage(sug)}
                className="whitespace-nowrap px-3 py-1.5 rounded-full bg-white border border-stone-200 text-stone-700 text-xs font-medium hover:bg-amber-50 hover:border-amber-300 transition-colors shadow-sm"
              >
                {sug}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Input Form Bar */}
      <footer className="p-3 bg-white border-t border-stone-200 shrink-0">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSendMessage();
          }}
          className="flex items-center gap-2"
        >
          <input
            type="text"
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            placeholder="Đặt câu hỏi về Chùa Linh Ứng..."
            disabled={loading}
            className="flex-1 px-4 py-3 rounded-xl border border-stone-300 bg-stone-50 text-stone-900 placeholder-stone-400 text-xs sm:text-sm focus:outline-none focus:ring-2 focus:ring-amber-500 focus:bg-white transition-all shadow-inner"
          />
          <button
            type="submit"
            disabled={loading || !inputText.trim()}
            className={`p-3 rounded-xl font-medium text-white transition-all flex items-center justify-center shadow-md ${
              inputText.trim() && !loading
                ? 'bg-amber-600 hover:bg-amber-700 active:scale-95'
                : 'bg-stone-300 cursor-not-allowed'
            }`}
            title="Gửi câu hỏi"
          >
            <Send className="w-4 h-4" />
          </button>
        </form>
      </footer>
    </div>
  );
}
