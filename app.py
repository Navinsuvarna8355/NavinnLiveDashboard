import React, { useState, useEffect } from 'react';

// This is a single-file React component that creates a trading dashboard.
// It shows mock trading signals based on EMA, PCR, and RSI for different indices.

const calculateEMA = (prices, period) => {
  if (!prices || prices.length < period) return null;
  const k = 2 / (period + 1);
  let ema = prices[0];
  for (let i = 1; i < prices.length; i++) {
    ema = prices[i] * k + ema * (1 - k);
  }
  return ema;
};

const indices = [
  { name: 'NIFTY 50', basePrice: 22500, volatility: 20 },
  { name: 'BANKNIFTY', basePrice: 48000, volatility: 50 },
  { name: 'FINNIFTY', basePrice: 21500, volatility: 30 },
];

const App = () => {
  const [selectedIndex, setSelectedIndex] = useState(indices[0]);
  const [spotPrice, setSpotPrice] = useState(0);
  const [strikePrice, setStrikePrice] = useState(0);
  const [emaSignal, setEmaSignal] = useState('Sideways');
  const [pcrSignal, setPcrSignal] = useState('Neutral');
  const [rsiSignal, setRsiSignal] = useState('Neutral');
  const [history, setHistory] = useState([]);

  // Mock data simulation for live market feed
  useEffect(() => {
    // This function creates the historical price data required to calculate the EMA.
    const generateInitialHistory = (basePrice, volatility) => {
      const initialPrices = [];
      let currentPrice = basePrice;
      for (let i = 0; i < 50; i++) {
        currentPrice += (Math.random() - 0.5) * volatility;
        initialPrices.push(currentPrice);
      }
      setHistory(initialPrices);
    };

    generateInitialHistory(selectedIndex.basePrice, selectedIndex.volatility);

    const interval = setInterval(() => {
      // Update the mock data
      setSpotPrice(prevPrice => prevPrice + (Math.random() - 0.5) * selectedIndex.volatility);
    }, 2000);

    return () => clearInterval(interval);
  }, [selectedIndex]);

  // Calculate indicators and signals whenever spotPrice changes
  useEffect(() => {
    if (spotPrice === 0) return;

    // Add new spot price to history and keep it at a reasonable length
    setHistory(prevHistory => {
      const newHistory = [...prevHistory, spotPrice].slice(-50);
      const latestPrices = newHistory;

      // Calculate EMAs
      const lowestEMA = calculateEMA(latestPrices, 3);
      const mediumEMA = calculateEMA(latestPrices, 13);
      const longestEMA = calculateEMA(latestPrices, 9);
      
      // Calculate Strike Price (simulated)
      setStrikePrice(Math.round(spotPrice / 50) * 50);

      // EMA Crossover Signal Logic (based on user's pine script)
      if (lowestEMA > mediumEMA && lowestEMA > longestEMA) {
        setEmaSignal('Buy (CE)');
      } else if (lowestEMA < mediumEMA && lowestEMA < longestEMA) {
        setEmaSignal('Sell (PE)');
      } else {
        setEmaSignal('Sideways');
      }

      // Simulate PCR
      const pcr = 0.8 + Math.random() * 0.4;
      if (pcr > 1.1) {
        setPcrSignal('Bullish');
      } else if (pcr < 0.9) {
        setPcrSignal('Bearish');
      } else {
        setPcrSignal('Neutral');
      }

      // Simulate RSI
      const rsi = 30 + Math.random() * 40;
      if (rsi > 70) {
        setRsiSignal('Overbought');
      } else if (rsi < 30) {
        setRsiSignal('Oversold');
      } else {
        setRsiSignal('Neutral');
      }

      return newHistory;
    });

  }, [spotPrice, selectedIndex]);

  const getSignalColor = (signal) => {
    switch (signal) {
      case 'Buy (CE)':
      case 'Bullish':
        return 'bg-green-600';
      case 'Sell (PE)':
      case 'Bearish':
        return 'bg-red-600';
      case 'Sideways':
      case 'Neutral':
      case 'Overbought':
      case 'Oversold':
        return 'bg-yellow-600';
      default:
        return 'bg-gray-500';
    }
  };

  return (
    <div className="bg-gray-900 min-h-screen text-white font-inter p-4 sm:p-8 flex flex-col items-center">
      <div className="container mx-auto max-w-4xl">
        <h1 className="text-4xl sm:text-5xl font-bold text-center mb-6 text-yellow-400">
          NSE Trading Dashboard
        </h1>
        <p className="text-center text-sm sm:text-base text-gray-400 mb-6">
          <span className="font-bold text-red-400">Warning:</span> This app is for educational purposes only. The data is simulated and should not be used for real trading decisions.
        </p>

        {/* Index selection dropdown */}
        <div className="flex justify-center mb-8">
          <select 
            className="p-3 bg-gray-800 text-white rounded-lg shadow-lg border border-gray-700 focus:outline-none focus:ring-2 focus:ring-yellow-500"
            value={selectedIndex.name}
            onChange={(e) => {
              const newIndex = indices.find(idx => idx.name === e.target.value);
              setSelectedIndex(newIndex);
            }}
          >
            {indices.map((index) => (
              <option key={index.name} value={index.name}>
                {index.name}
              </option>
            ))}
          </select>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 mb-8 text-center">
          <div className="bg-gray-800 p-6 rounded-2xl shadow-lg border border-gray-700">
            <h2 className="text-xl sm:text-2xl font-semibold text-gray-300">Spot Price</h2>
            <p className="text-3xl sm:text-4xl font-bold mt-2 text-white">₹{spotPrice.toFixed(2)}</p>
          </div>
          <div className="bg-gray-800 p-6 rounded-2xl shadow-lg border border-gray-700">
            <h2 className="text-xl sm:text-2xl font-semibold text-gray-300">Strike Price</h2>
            <p className="text-3xl sm:text-4xl font-bold mt-2 text-white">₹{strikePrice.toFixed(2)}</p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-gray-800 p-6 rounded-2xl shadow-lg border border-gray-700 text-center">
            <h3 className="text-xl font-semibold text-gray-300">EMA Signal</h3>
            <div className={`p-4 mt-4 rounded-xl font-bold text-lg ${getSignalColor(emaSignal)}`}>
              {emaSignal}
            </div>
          </div>
          <div className="bg-gray-800 p-6 rounded-2xl shadow-lg border border-gray-700 text-center">
            <h3 className="text-xl font-semibold text-gray-300">PCR Signal</h3>
            <div className={`p-4 mt-4 rounded-xl font-bold text-lg ${getSignalColor(pcrSignal)}`}>
              {pcrSignal}
            </div>
          </div>
          <div className="bg-gray-800 p-6 rounded-2xl shadow-lg border border-gray-700 text-center">
            <h3 className="text-xl font-semibold text-gray-300">RSI Signal</h3>
            <div className={`p-4 mt-4 rounded-xl font-bold text-lg ${getSignalColor(rsiSignal)}`}>
              {rsiSignal}
            </div>
          </div>
        </div>

        <div className="mt-8 text-center text-gray-400">
          <p className="text-sm">This app simulates live NSE data and is for demonstration purposes only.</p>
        </div>
      </div>
    </div>
  );
};

export default App;
