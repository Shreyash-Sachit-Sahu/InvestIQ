"use client"

import { motion } from "framer-motion"
import SummaryCard from "@/components/SummaryCard"
import PortfolioTable from "@/components/PortfolioTable"
import Chart from "@/components/Chart"
import { useState } from "react"
import PortfolioImportDialog from "@/components/PortfolioImportDialog"
import { Button } from "@/components/ui/button"

export default function Dashboard() {
  const [portfolioData, setPortfolioData] = useState([])
  const [chartData, setChartData] = useState({
    labels: [],
    datasets: [],
  })
  const [isImportDialogOpen, setIsImportDialogOpen] = useState(false)
  const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || '';

  const handleImportPortfolio = async (method: string, data?: File) => {
  if (method !== 'csv' || !data) {
    console.warn('Import method not supported or no data provided');
    setIsImportDialogOpen(false);
    return;
  }

  try {
    const token = localStorage.getItem('access_token');
    if (!token) {
      alert('Not authenticated. Please log in.');
      setIsImportDialogOpen(false);
      return;
    }

    const formData = new FormData();
    formData.append('portfolio_csv', data);

    const response = await fetch('${API_BASE_URL}/portfolio/upload-csv', {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${token}`
      },
      body: formData
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      const message = errorData.error || `Upload failed with status ${response.status}`;
      alert(message);
    } else {
      const result = await response.json();
      console.log('Import successful:', result);
      if (result.errors && result.errors.length > 0) {
        alert('Some rows had errors:\n' + result.errors.join('\n'));
      } else {
        alert('Portfolio imported successfully!');
      }
      // TODO: Optionally refresh your holdings here
    }
  } catch (error: any) {
    console.error('Error importing portfolio:', error);
    alert(error.message || 'Import failed');
  } finally {
    setIsImportDialogOpen(false);
  }
};


  return (
    <div className="container mx-auto px-4 py-8">
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6 }}>
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900">NSE Portfolio Dashboard</h1>
          <Button onClick={() => setIsImportDialogOpen(true)} className="btn-primary">
            Import Portfolio
          </Button>
        </div>

        {/* Summary Cards */}
        <div className="grid md:grid-cols-3 gap-6 mb-8">
          <SummaryCard title="Total Portfolio Value" value="₹0.00" delta={0} />
          <SummaryCard title="Risk Score" value="--" delta={0} />
          <SummaryCard title="Predicted Return" value="--%" delta={0} />
        </div>

        {/* Prediction Chart */}
        <div className="card mb-8">
          <h2 className="text-xl font-semibold mb-4">NSE Portfolio Performance Prediction</h2>
          <Chart labels={chartData.labels} data={chartData.datasets} type="line" />
        </div>

        {/* Portfolio Table */}
        <div className="card">
          <h2 className="text-xl font-semibold mb-4">Current NSE Holdings</h2>
          <PortfolioTable data={portfolioData} onImportClick={() => setIsImportDialogOpen(true)} />
        </div>
      </motion.div>

      <PortfolioImportDialog
        isOpen={isImportDialogOpen}
        onClose={() => setIsImportDialogOpen(false)}
        onImport={handleImportPortfolio}
      />
    </div>
  )
}
