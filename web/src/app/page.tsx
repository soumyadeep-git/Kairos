"use client";

import { useState, useCallback } from "react";
import dynamic from "next/dynamic";

const VoiceAgent = dynamic(() => import("@/components/VoiceAgent"), {
  ssr: false,
  loading: () => (
    <div className="min-h-screen bg-background flex items-center justify-center relative overflow-hidden">
      <div className="fixed inset-0 bg-noise opacity-50 pointer-events-none" />
      <div className="flex flex-col items-center gap-6 animate-float">
        <div className="w-20 h-20 bg-accent rounded-full border-2 border-border flex items-center justify-center shadow-sketch animate-spin-slow">
           <span className="text-4xl">⏳</span>
        </div>
        <p className="font-serif text-2xl text-foreground">Summoning Kairos...</p>
      </div>
    </div>
  ),
});

type ConnectionState = "disconnected" | "connecting" | "connected";

export default function Home() {
  const [connectionState, setConnectionState] =
    useState<ConnectionState>("disconnected");
  const [token, setToken] = useState<string | null>(null);
  const [serverUrl, setServerUrl] = useState<string | null>(null);
  const [userName, setUserName] = useState("");
  const [error, setError] = useState<string | null>(null);

  const generateRoomName = () => {
    return `kairos-${Date.now()}-${Math.random().toString(36).substring(2, 8)}`;
  };

  const handleConnect = useCallback(async () => {
    if (!userName.trim()) {
      setError("Please tell us who you are!");
      return;
    }

    setError(null);
    setConnectionState("connecting");

    try {
      const roomName = generateRoomName();
      const response = await fetch(
        `/api/token?room=${encodeURIComponent(roomName)}&username=${encodeURIComponent(userName)}`
      );

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.error || "Failed to get token");
      }

      const data = await response.json();
      setToken(data.token);
      setServerUrl(data.url);
      setConnectionState("connected");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Connection failed");
      setConnectionState("disconnected");
    }
  }, [userName]);

  const handleDisconnect = useCallback(() => {
    setToken(null);
    setServerUrl(null);
    setConnectionState("disconnected");
  }, []);

  if (connectionState === "connected" && token && serverUrl) {
    return (
      <VoiceAgent
        token={token}
        serverUrl={serverUrl}
        onDisconnect={handleDisconnect}
      />
    );
  }

  return (
    <div className="min-h-screen bg-background relative overflow-hidden flex flex-col font-sans">
      {/* Texture Overlay */}
      <div className="fixed inset-0 bg-noise opacity-40 pointer-events-none z-50 mix-blend-multiply" />
      
      {/* Decorative Background Elements */}
      <div className="absolute top-[-10%] right-[-5%] w-[500px] h-[500px] bg-[#FFD233] rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-float" />
      <div className="absolute bottom-[-10%] left-[-5%] w-[400px] h-[400px] bg-[#FF9F1C] rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-float-delay" />

      {/* Shapes */}
      <div className="absolute top-20 left-10 w-12 h-12 border-2 border-border rounded-full flex items-center justify-center animate-float-delay rotate-12">
        <div className="w-3 h-3 bg-foreground rounded-full" />
      </div>
      <div className="absolute bottom-40 right-20 w-16 h-16 border-2 border-border rotate-45 animate-float flex items-center justify-center">
         <div className="w-full h-0.5 bg-border" />
         <div className="h-full w-0.5 bg-border absolute" />
      </div>

      {/* Header */}
      <header className="relative z-10 w-full p-8 flex justify-between items-center max-w-7xl mx-auto">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-foreground text-background flex items-center justify-center rounded-lg border-2 border-transparent rotate-3 hover:rotate-0 transition-all cursor-default">
            <span className="font-serif font-bold text-xl">K</span>
          </div>
          <span className="font-serif text-2xl font-bold text-foreground tracking-tight">Kairos</span>
        </div>
        <div className="px-4 py-2 bg-white border-2 border-border rounded-full shadow-sketch-sm flex items-center gap-2">
          <div className="w-2.5 h-2.5 bg-success rounded-full border border-border animate-pulse" />
          <span className="text-sm font-bold text-foreground">System Online</span>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 flex flex-col items-center justify-center relative z-10 px-4 py-10">
        <div className="max-w-4xl w-full flex flex-col md:flex-row items-center gap-12 md:gap-20">
          
          {/* Left: Copy */}
          <div className="flex-1 text-center md:text-left space-y-6">
            <div className="inline-block px-4 py-1.5 bg-accent/20 border border-border rounded-full rotate-[-2deg] mb-2">
              <span className="text-sm font-bold text-foreground uppercase tracking-wider">Voice AI Assistant</span>
            </div>
            
            <h1 className="text-6xl md:text-7xl font-serif text-foreground leading-[0.9]">
              Time is <br/>
              <span className="italic text-accent drop-shadow-[2px_2px_0px_#4A3B32]">yours</span> again.
            </h1>
            
            <p className="text-lg md:text-xl text-muted font-medium max-w-md mx-auto md:mx-0 leading-relaxed">
              Schedule appointments, manage your calendar, and get organized just by talking. Naturally.
            </p>

            {/* Feature Pills */}
            <div className="flex flex-wrap gap-3 justify-center md:justify-start pt-2">
              {['🎙️ Natural Voice', '📅 Smart Booking', '🔒 Private'].map((feat, i) => (
                <div key={i} className="px-3 py-1.5 bg-white border-2 border-border rounded-lg shadow-sketch-sm text-sm font-bold hover:-translate-y-0.5 transition-transform cursor-default">
                  {feat}
                </div>
              ))}
            </div>
          </div>

          {/* Right: Login Card */}
          <div className="w-full max-w-md relative">
            {/* Card Decor */}
            <div className="absolute -top-6 -right-6 w-20 h-20 bg-accent rounded-full border-2 border-border -z-10" />
            <div className="absolute -bottom-4 -left-4 w-full h-full bg-foreground rounded-3xl -z-10 opacity-10" />
            
            <div className="card-trendy bg-white transform rotate-2 hover:rotate-0 transition-transform duration-500">
              <div className="mb-8 text-center">
                 <h2 className="text-3xl mb-2">Hello there!</h2>
                 <p className="text-muted">Ready to organize your life?</p>
              </div>

              <div className="space-y-6">
                <div className="space-y-2">
                  <label htmlFor="name" className="text-sm font-bold text-foreground uppercase tracking-wide ml-1">
                    What should we call you?
                  </label>
                  <input
                    type="text"
                    id="name"
                    value={userName}
                    onChange={(e) => setUserName(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && handleConnect()}
                    placeholder="e.g. Alex"
                    className="input-trendy"
                    autoComplete="off"
                  />
                </div>

                {error && (
                  <div className="p-4 bg-error/10 border-2 border-error text-error rounded-xl text-sm font-medium flex items-center gap-2 animate-bounce-soft">
                    <span>🚨</span> {error}
                  </div>
                )}

                <button
                  onClick={handleConnect}
                  disabled={connectionState === "connecting"}
                  className="btn-trendy w-full group"
                >
                  <div className="flex items-center justify-center gap-3">
                    {connectionState === "connecting" ? (
                      <>
                        <div className="w-5 h-5 border-2 border-foreground border-t-transparent rounded-full animate-spin" />
                        <span>Connecting...</span>
                      </>
                    ) : (
                      <>
                        <span>Start Conversation</span>
                        <span className="group-hover:translate-x-1 transition-transform">→</span>
                      </>
                    )}
                  </div>
                </button>
              </div>
              
              <div className="mt-6 pt-6 border-t-2 border-dashed border-border/30 text-center">
                 <p className="text-xs font-bold text-muted uppercase tracking-widest">Powered by LiveKit</p>
              </div>
            </div>
          </div>

        </div>
      </main>
      
      {/* Footer */}
      <footer className="relative z-10 w-full py-6 text-center text-sm font-medium text-muted/60">
        <p>© 2026 Kairos. Crafted with intent.</p>
      </footer>
    </div>
  );
}
