import { Component, ErrorInfo, ReactNode } from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Uncaught error:', error, errorInfo);
  }

  public render() {
    if (this.state.hasError) {
      return (
        <div className="p-8 max-w-2xl mx-auto my-12 bg-slate-900 border border-red-500/30 rounded-2xl p-6 text-center shadow-2xl">
          <div className="w-12 h-12 rounded-full bg-red-500/10 text-red-400 mx-auto mb-4 flex items-center justify-center">
            <AlertTriangle className="w-6 h-6" />
          </div>
          <h2 className="text-xl font-bold text-white mb-2">Đã xảy ra lỗi hiển thị giao diện</h2>
          <p className="text-sm text-slate-400 mb-6 font-mono text-left bg-slate-950 p-4 rounded-xl overflow-x-auto text-red-300">
            {this.state.error?.message || 'Lỗi không xác định'}
          </p>
          <button
            onClick={() => window.location.reload()}
            className="inline-flex items-center space-x-2 px-5 py-2.5 bg-amber-500 hover:bg-amber-600 text-slate-950 font-semibold rounded-xl cursor-pointer"
          >
            <RefreshCw className="w-4 h-4" />
            <span>Tải lại trang</span>
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}
