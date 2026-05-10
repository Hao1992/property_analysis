import axios from 'axios'
import type { AnalyzeRequest, AnalyzeResponse, CompareRequest, CompareResponse } from '../types/analysis'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '',
  headers: { 'Content-Type': 'application/json' }
})

export async function analyzeProperty(req: AnalyzeRequest): Promise<AnalyzeResponse> {
  const { data } = await api.post<AnalyzeResponse>('/analyze', req)
  return data
}

export async function compareProperties(req: CompareRequest): Promise<CompareResponse> {
  const { data } = await api.post<CompareResponse>('/compare', req)
  return data
}

export async function healthCheck(): Promise<{ status: string }> {
  const { data } = await api.get('/health')
  return data
}
