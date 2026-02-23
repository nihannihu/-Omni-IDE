"use client";

import React, { useState, useEffect } from 'react';

// Setup state types
interface SetupStatus {
    ram_gb: number;
    recommendation: string;
    ollama_running: boolean;
    models: string[];
    has_gemini_key: boolean;
}

export default function OnboardingWizard() {
    const [status, setStatus] = useState<SetupStatus | null>(null);
    const [loading, setLoading] = useState(true);
    const [showWizard, setShowWizard] = useState(false);
    const [geminiKey, setGeminiKey] = useState('');
    const [savingKey, setSavingKey] = useState(false);
    const [installingLocal, setInstallingLocal] = useState(false);
    const [installProgress, setInstallProgress] = useState('');

    useEffect(() => {
        checkStatus();
    }, []);

    const checkStatus = async () => {
        try {
            const res = await fetch('http://localhost:8000/api/setup/status');
            const data = await res.json();
            setStatus(data);
            // QA Check: ALWAYS show wizard on fresh install (no Gemini key in .env),
            // even if Ollama models survived an uninstall.
            if (!data.has_gemini_key) {
                setShowWizard(true);
            }
        } catch (e) {
            console.error("Failed to fetch setup status", e);
        } finally {
            setLoading(false);
        }
    };

    const pollProgress = async () => {
        try {
            const res = await fetch('http://localhost:8000/api/setup/progress');
            const data = await res.json();
            setInstallProgress(data.message);

            if (data.status === 'completed' || data.status === 'error') {
                setInstallingLocal(false);
                if (data.status === 'completed') {
                    // Wait slightly, then save the key in case they typed it
                    if (geminiKey) {
                        await saveKeySilently();
                    } else {
                        setTimeout(() => {
                            setShowWizard(false);
                            window.location.reload();
                        }, 2000);
                    }
                }
                return false;
            }
            return true;
        } catch (e) {
            return false;
        }
    };

    const saveKeySilently = async () => {
        try {
            await fetch('http://localhost:8000/api/setup/save_key', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ key: geminiKey })
            });
            setShowWizard(false);
            window.location.reload();
        } catch (e) {
            console.error(e);
        }
    };

    const handleInstallLocal = async (model: string) => {
        setInstallingLocal(true);
        setInstallProgress(`Starting download for ${model}...`);
        try {
            await fetch('http://localhost:8000/api/setup/install_local', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ model_name: model })
            });

            const pollInterval = setInterval(async () => {
                const shouldContinue = await pollProgress();
                if (!shouldContinue) clearInterval(pollInterval);
            }, 1000);

        } catch (e) {
            setInstallingLocal(false);
            setInstallProgress("Failed to start installation.");
        }
    };

    const handleSaveKey = async () => {
        if (!geminiKey) return;
        setSavingKey(true);
        await saveKeySilently();
        setSavingKey(false);
    };

    if (loading || !showWizard || !status) return null;

    return (
        <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/80 backdrop-blur-sm">
            <div className="bg-[#1e1e1e] border border-gray-700 rounded-lg p-8 max-w-2xl w-full shadow-2xl text-gray-200">
                <h2 className="text-3xl font-bold mb-2 text-white">Smart Engine Setup</h2>
                <p className="text-gray-400 mb-6">Omni-IDE requires an AI engine config. Let's optimize for your hardware.</p>

                <div className="bg-[#252526] p-4 rounded mb-6 border border-gray-700 flex items-center justify-between">
                    <div>
                        <p className="font-semibold text-white">🔍 System Scan</p>
                        <p className="text-sm">Detected {status.ram_gb}GB RAM</p>
                    </div>
                    <div className="text-right">
                        <p className="font-semibold text-white">🧠 Local Daemon (Ollama)</p>
                        <p className={`text-sm ${status.ollama_running ? 'text-green-400' : 'text-red-400'}`}>
                            {status.ollama_running ? '🟢 Active & Ready' : '🔴 Not Detected / Offline'}
                        </p>
                    </div>
                </div>

                {/* Global Key Input Required for Both */}
                <div className="mb-6">
                    <p className="font-semibold text-white mb-2">🔑 Gemini Cloud Intelligence (Required)</p>
                    <p className="text-xs text-gray-400 mb-2">Gemini acts as the brain for rigid tool-calling and orchestration.</p>
                    <input
                        type="password"
                        placeholder="Paste Gemini API Key"
                        className="w-full bg-[#3c3c3c] text-white px-3 py-2 rounded border border-gray-600 focus:outline-none focus:border-blue-500 text-sm"
                        value={geminiKey}
                        onChange={(e) => setGeminiKey(e.target.value)}
                    />
                </div>

                <div className="grid grid-cols-2 gap-6">
                    {/* Card 1: Cloud */}
                    <div className={`bg-[#252526] p-6 rounded-lg border ${status.recommendation === 'CLOUD_ONLY' ? 'border-blue-500' : 'border-gray-700'} flex flex-col relative overflow-hidden`}>
                        {status.recommendation === 'CLOUD_ONLY' && (
                            <div className="absolute top-0 right-0 bg-blue-600 text-xs px-2 py-1 rounded-bl font-bold text-white">Recommended</div>
                        )}
                        <h3 className="text-xl font-bold text-blue-400 mb-2">⚡ Cloud Speed</h3>
                        <p className="text-sm text-gray-400 mb-4 flex-grow">
                            Instant start. No downloads required. Zero local hardware overhead. Full speed.
                        </p>
                        <button
                            onClick={handleSaveKey}
                            disabled={savingKey || !geminiKey}
                            className="w-full py-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white rounded font-medium transition-colors mt-auto"
                        >
                            {savingKey ? 'Saving...' : 'Use Cloud Only'}
                        </button>
                    </div>

                    {/* Card 2: Hybrid */}
                    <div className={`bg-[#252526] p-6 rounded-lg border ${status.recommendation.startsWith('HYBRID') ? 'border-green-500' : 'border-gray-700'} flex flex-col relative overflow-hidden`}>
                        {status.recommendation.startsWith('HYBRID') && (
                            <div className="absolute top-0 right-0 bg-green-600 text-xs px-2 py-1 rounded-bl font-bold text-white">Recommended</div>
                        )}
                        <h3 className="text-xl font-bold text-green-400 mb-2">🚀 Hybrid Power</h3>
                        <p className="text-sm text-gray-400 mb-4 flex-grow">
                            Offline-capable fallback combined with Cloud intelligence. High privacy.
                        </p>

                        {!status.ollama_running ? (
                            <div className="text-xs text-red-400 mb-4 p-2 bg-red-900/30 rounded border border-red-800">
                                ⚠️ Ollama daemon not running. Please install Ollama on port 11434 to enable Hybrid features.
                            </div>
                        ) : (
                            <div className="mb-4">
                                <p className="text-xs text-gray-500 mb-1">Recommended Profile ({status.ram_gb}GB RAM):</p>
                                <p className="font-mono text-xs bg-[#1e1e1e] p-2 rounded border border-gray-700 text-green-300">
                                    {status.recommendation === 'HYBRID_PRO' ? 'qwen2.5-coder:7b (4.7 GB)' : 'qwen2.5-coder:3b (1.9 GB)'}
                                </p>
                            </div>
                        )}

                        <div className="mt-auto">
                            {installingLocal ? (
                                <div className="w-full py-2 bg-[#3c3c3c] text-center text-gray-300 rounded text-xs font-mono truncate px-2 border border-blue-500/50">
                                    {installProgress || 'Initializing Model...'}
                                </div>
                            ) : (
                                <button
                                    onClick={() => handleInstallLocal(status.recommendation === 'HYBRID_PRO' ? 'qwen2.5-coder:7b' : 'qwen2.5-coder:3b')}
                                    disabled={!status.ollama_running || !geminiKey}
                                    className="w-full py-2 bg-green-700 hover:bg-green-600 disabled:opacity-50 disabled:bg-gray-700 text-white rounded font-medium transition-colors"
                                >
                                    Install Hybrid
                                </button>
                            )}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
