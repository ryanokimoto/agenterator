import React from 'react';

function App() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      {/* Navigation */}
      <nav className="bg-white shadow-md">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <h1 className="text-2xl font-bold text-indigo-600">🧠 RAG Platform</h1>
            </div>
            <div className="flex items-center space-x-4">
              <button className="text-gray-700 hover:text-indigo-600 px-3 py-2 rounded-md text-sm font-medium">
                Features
              </button>
              <button className="text-gray-700 hover:text-indigo-600 px-3 py-2 rounded-md text-sm font-medium">
                About
              </button>
              <button className="bg-indigo-600 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-indigo-700">
                Get Started
              </button>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-20 pb-16">
        <div className="text-center">
          <h2 className="text-5xl font-bold text-gray-900 mb-6">
            Transform Your Documents into
            <span className="text-indigo-600"> AI Agents</span>
          </h2>
          <p className="text-xl text-gray-600 mb-8 max-w-3xl mx-auto">
            Upload lectures, PDFs, videos, and more to create intelligent AI assistants 
            that understand your content deeply. Perfect for students, researchers, and professionals.
          </p>
          <div className="space-x-4">
            <button className="bg-indigo-600 text-white px-8 py-3 rounded-lg text-lg font-semibold hover:bg-indigo-700 transform hover:scale-105 transition">
              Try Demo
            </button>
            <button className="bg-white text-indigo-600 px-8 py-3 rounded-lg text-lg font-semibold border-2 border-indigo-600 hover:bg-indigo-50">
              Learn More
            </button>
          </div>
        </div>
      </div>

      {/* Feature Cards */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <h3 className="text-3xl font-bold text-center text-gray-900 mb-12">
          Key Features
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {/* Feature 1 */}
          <div className="bg-white p-6 rounded-lg shadow-md hover:shadow-xl transition">
            <div className="text-4xl mb-4">📄</div>
            <h4 className="text-xl font-semibold mb-2">Multi-Format Support</h4>
            <p className="text-gray-600">
              Process PDFs, videos, PowerPoints, Word docs, and more with our advanced parsers.
            </p>
          </div>

          {/* Feature 2 */}
          <div className="bg-white p-6 rounded-lg shadow-md hover:shadow-xl transition">
            <div className="text-4xl mb-4">🤖</div>
            <h4 className="text-xl font-semibold mb-2">Intelligent RAG</h4>
            <p className="text-gray-600">
              State-of-the-art retrieval augmented generation for accurate, contextual responses.
            </p>
          </div>

          {/* Feature 3 */}
          <div className="bg-white p-6 rounded-lg shadow-md hover:shadow-xl transition">
            <div className="text-4xl mb-4">⚡</div>
            <h4 className="text-xl font-semibold mb-2">Real-time Processing</h4>
            <p className="text-gray-600">
              Watch your documents transform into AI agents with live progress updates.
            </p>
          </div>
        </div>
      </div>

      {/* Status Check */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="bg-green-50 border border-green-200 rounded-lg p-4 text-center">
          <p className="text-green-800 font-semibold">
            ✅ Frontend is working! React + Tailwind CSS are properly configured.
          </p>
          <p className="text-green-600 text-sm mt-2">
            {new Date().toLocaleString()} - Development Server Running
          </p>
        </div>
      </div>

      {/* Footer */}
      <footer className="bg-gray-800 text-white py-8 mt-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <p className="text-gray-400">
            © 2024 RAG Platform. Built with React, FastAPI, and LangChain.
          </p>
        </div>
      </footer>
    </div>
  );
}

export default App;