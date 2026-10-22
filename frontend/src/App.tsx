import { Route, Routes } from 'react-router-dom'
import { Header } from './components/Header'
import { useTheme } from './hooks/useTheme'
import { CalculatorPage } from './pages/CalculatorPage'
import { SharePage } from './pages/SharePage'

export function App() {
  const [theme, toggleTheme] = useTheme()
  return (
    <>
      <Header theme={theme} onToggleTheme={toggleTheme} />
      <Routes>
        <Route path="/" element={<CalculatorPage theme={theme} />} />
        <Route path="/s/:slug" element={<SharePage theme={theme} />} />
        <Route path="*" element={<CalculatorPage theme={theme} />} />
      </Routes>
    </>
  )
}
