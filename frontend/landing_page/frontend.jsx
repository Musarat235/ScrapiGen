import React, { useState } from 'react';
import { Search, Code, Zap, Globe, Star, Users, ArrowRight, Play, Check } from 'lucide-react';

export default function ApifyInterface() {
  const [searchQuery, setSearchQuery] = useState('');
  const [isDark, setIsDark] = useState(true);

  const actors = [
    {
      name: 'TikTok Scraper',
      author: 'clockworks',
      description: 'Extract data from TikTok videos, hashtags, and users. Use URLs or search queries to scrape profiles, posts, and music data.',
      runs: '92K',
      rating: 4.7,
      color: 'from-pink-500 to-purple-500'
    },
    {
      name: 'Google Maps Scraper',
      author: 'compass',
      description: 'Extract data from thousands of Google Maps locations and businesses, including reviews, contact info, and opening hours.',
      runs: '201K',
      rating: 4.8,
      color: 'from-blue-500 to-green-500'
    },
    {
      name: 'Instagram Scraper',
      author: 'apify',
      description: 'Scrape and download Instagram posts, profiles, places, hashtags, photos, and comments.',
      runs: '147K',
      rating: 4.6,
      color: 'from-purple-500 to-pink-500'
    },
    {
      name: 'Website Content Crawler',
      author: 'apify',
      description: 'Crawl websites and extract text content to feed AI models, LLM applications, and vector databases.',
      runs: '86K',
      rating: 4.6,
      color: 'from-orange-500 to-red-500'
    },
    {
      name: 'Amazon Scraper',
      author: 'junglee',
      description: 'Gets product data from Amazon including reviews, prices, descriptions, and ASIN.',
      runs: '9K',
      rating: 5.0,
      color: 'from-yellow-500 to-orange-500'
    },
    {
      name: 'Facebook Posts Scraper',
      author: 'apify',
      description: 'Extract data from hundreds of Facebook posts from pages and profiles.',
      runs: '36K',
      rating: 4.6,
      color: 'from-blue-600 to-blue-400'
    }
  ];

  const companies = [
    'T-Mobile', 'Decathlon', 'Accenture', 'Microsoft', 'Square', 'Siemens'
  ];

  const features = [
    {
      icon: <Globe className="w-8 h-8" />,
      title: 'Marketplace of 7,000+ Actors',
      description: 'Apify has Actors for scraping websites, automating the web, and feeding AI with web data.',
      cta: 'Visit Store'
    },
    {
      icon: <Code className="w-8 h-8" />,
      title: 'Build and deploy your own',
      description: 'Start building new Actors with our code templates and extensive guides.',
      cta: 'Start building'
    },
    {
      icon: <Users className="w-8 h-8" />,
      title: 'Or we can build it for you',
      description: 'Rely on our experts to deliver and maintain custom web scraping solutions.',
      cta: 'Learn more'
    }
  ];

  return (
    <div className={`min-h-screen ${isDark ? 'bg-gray-900 text-white' : 'bg-white text-gray-900'}`}>
      {/* Header */}
      <header className={`border-b ${isDark ? 'border-gray-800' : 'border-gray-200'}`}>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center space-x-8">
              <div className="flex items-center space-x-2">
                <div className="w-8 h-8 bg-gradient-to-br from-orange-500 to-pink-500 rounded-lg flex items-center justify-center">
                  <Zap className="w-5 h-5 text-white" />
                </div>
                <span className="text-xl font-bold">Apify</span>
              </div>
              <nav className="hidden md:flex space-x-6">
                <a href="#" className="hover:text-orange-500 transition">Products</a>
                <a href="#" className="hover:text-orange-500 transition">Solutions</a>
                <a href="#" className="hover:text-orange-500 transition">Developers</a>
                <a href="#" className="hover:text-orange-500 transition">Pricing</a>
              </nav>
            </div>
            <div className="flex items-center space-x-4">
              <button
                onClick={() => setIsDark(!isDark)}
                className={`p-2 rounded-lg ${isDark ? 'bg-gray-800' : 'bg-gray-100'}`}
              >
                {isDark ? '☀️' : '🌙'}
              </button>
              <button className="px-4 py-2 rounded-lg hover:bg-gray-800 transition">
                Sign in
              </button>
              <button className="px-4 py-2 bg-gradient-to-r from-orange-500 to-pink-500 rounded-lg hover:shadow-lg transition">
                Start free
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-orange-500/10 via-purple-500/10 to-pink-500/10" />
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20 relative">
          <div className="text-center max-w-4xl mx-auto">
            <div className={`inline-flex items-center space-x-2 px-4 py-2 rounded-full mb-6 ${isDark ? 'bg-gray-800' : 'bg-gray-100'}`}>
              <span className="text-sm font-semibold text-orange-500">New</span>
              <span className="text-sm">Join the Apify $1M Challenge. Build to win!</span>
            </div>
            <h1 className="text-5xl md:text-6xl font-bold mb-6 bg-gradient-to-r from-orange-500 via-purple-500 to-pink-500 bg-clip-text text-transparent">
              Get real-time web data for your AI
            </h1>
            <p className={`text-xl mb-8 ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
              Apify Actors scrape up-to-date web data from any website for AI apps and agents, 
              social media monitoring, competitive intelligence, lead generation, and product research.
            </p>
            <div className="flex justify-center space-x-4">
              <button className="px-8 py-4 bg-gradient-to-r from-orange-500 to-pink-500 rounded-lg font-semibold hover:shadow-2xl transition flex items-center space-x-2">
                <span>Start for free</span>
                <ArrowRight className="w-5 h-5" />
              </button>
              <button className={`px-8 py-4 rounded-lg font-semibold transition flex items-center space-x-2 ${isDark ? 'bg-gray-800 hover:bg-gray-700' : 'bg-gray-100 hover:bg-gray-200'}`}>
                <Play className="w-5 h-5" />
                <span>Watch demo</span>
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* Popular Actors */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {actors.map((actor, idx) => (
            <div
              key={idx}
              className={`rounded-xl p-6 transition hover:scale-105 cursor-pointer ${isDark ? 'bg-gray-800 hover:bg-gray-750' : 'bg-gray-50 hover:bg-gray-100'}`}
            >
              <div className="flex items-start space-x-4 mb-4">
                <div className={`w-16 h-16 rounded-xl bg-gradient-to-br ${actor.color} flex items-center justify-center`}>
                  <Code className="w-8 h-8 text-white" />
                </div>
                <div className="flex-1">
                  <h3 className="font-bold text-lg mb-1">{actor.name}</h3>
                  <p className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                    {actor.author}
                  </p>
                </div>
              </div>
              <p className={`text-sm mb-4 ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
                {actor.description}
              </p>
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-4">
                  <span className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                    {actor.runs}
                  </span>
                  <div className="flex items-center space-x-1">
                    <Star className="w-4 h-4 fill-yellow-500 text-yellow-500" />
                    <span className="text-sm font-semibold">{actor.rating}</span>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
        <div className="text-center mt-10">
          <button className="px-8 py-3 bg-gradient-to-r from-orange-500 to-pink-500 rounded-lg font-semibold hover:shadow-xl transition">
            Browse 7,000+ Actors
          </button>
        </div>
      </section>

      {/* Trusted By Section */}
      <section className={`py-16 ${isDark ? 'bg-gray-800/50' : 'bg-gray-50'}`}>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <h2 className={`text-center text-sm font-semibold uppercase tracking-wider mb-8 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
            Trusted by global technology leaders
          </h2>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-8 items-center">
            {companies.map((company, idx) => (
              <div key={idx} className={`text-center font-semibold ${isDark ? 'text-gray-400' : 'text-gray-600'} hover:text-orange-500 transition cursor-pointer`}>
                {company}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
        <h2 className="text-4xl font-bold text-center mb-4">Not just a web scraping API</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mt-12">
          {features.map((feature, idx) => (
            <div
              key={idx}
              className={`rounded-xl p-8 transition hover:scale-105 cursor-pointer ${isDark ? 'bg-gray-800' : 'bg-gray-50'}`}
            >
              <div className="text-orange-500 mb-4">{feature.icon}</div>
              <h3 className="text-xl font-bold mb-3">{feature.title}</h3>
              <p className={`mb-4 ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
                {feature.description}
              </p>
              <button className="text-orange-500 font-semibold hover:underline flex items-center space-x-2">
                <span>{feature.cta}</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          ))}
        </div>
      </section>

      {/* Code Example Section */}
      <section className={`py-20 ${isDark ? 'bg-gray-800/50' : 'bg-gray-50'}`}>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <h2 className="text-4xl font-bold text-center mb-12">Build and deploy reliable scrapers</h2>
          <div className={`rounded-xl p-6 ${isDark ? 'bg-gray-900' : 'bg-white'} border ${isDark ? 'border-gray-700' : 'border-gray-200'}`}>
            <div className="flex space-x-4 mb-4">
              <button className="px-4 py-2 bg-gradient-to-r from-orange-500 to-pink-500 rounded-lg font-semibold text-sm">
                JavaScript
              </button>
              <button className={`px-4 py-2 rounded-lg font-semibold text-sm ${isDark ? 'hover:bg-gray-800' : 'hover:bg-gray-100'}`}>
                Python
              </button>
            </div>
            <pre className={`text-sm overflow-x-auto ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
              <code>{`import { PuppeteerCrawler, Dataset } from "crawlee";

const crawler = new PuppeteerCrawler({
  async requestHandler({ request, page, enqueueLinks }) {
    await Dataset.pushData({
      url: request.url,
      title: await page.title(),
    });
    await enqueueLinks();
  },
});

await crawler.run(["https://crawlee.dev"]);`}</code>
            </pre>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className={`border-t ${isDark ? 'border-gray-800' : 'border-gray-200'} py-12`}>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
            <div>
              <h4 className="font-bold mb-4">Products</h4>
              <ul className={`space-y-2 text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                <li><a href="#" className="hover:text-orange-500">Actors</a></li>
                <li><a href="#" className="hover:text-orange-500">Platform</a></li>
                <li><a href="#" className="hover:text-orange-500">Services</a></li>
              </ul>
            </div>
            <div>
              <h4 className="font-bold mb-4">Developers</h4>
              <ul className={`space-y-2 text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                <li><a href="#" className="hover:text-orange-500">Documentation</a></li>
                <li><a href="#" className="hover:text-orange-500">API</a></li>
                <li><a href="#" className="hover:text-orange-500">Academy</a></li>
              </ul>
            </div>
            <div>
              <h4 className="font-bold mb-4">Company</h4>
              <ul className={`space-y-2 text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                <li><a href="#" className="hover:text-orange-500">About</a></li>
                <li><a href="#" className="hover:text-orange-500">Blog</a></li>
                <li><a href="#" className="hover:text-orange-500">Careers</a></li>
              </ul>
            </div>
            <div>
              <h4 className="font-bold mb-4">Connect</h4>
              <ul className={`space-y-2 text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                <li><a href="#" className="hover:text-orange-500">Discord</a></li>
                <li><a href="#" className="hover:text-orange-500">Twitter</a></li>
                <li><a href="#" className="hover:text-orange-500">GitHub</a></li>
              </ul>
            </div>
          </div>
          <div className={`mt-12 pt-8 border-t ${isDark ? 'border-gray-800 text-gray-400' : 'border-gray-200 text-gray-600'} text-sm text-center`}>
            <p>© 2024 Apify Technologies. All rights reserved.</p>
          </div>
        </div>
      </footer>
    </div>
  );
}