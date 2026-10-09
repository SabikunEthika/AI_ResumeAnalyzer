
const API_BASE_URL = 'http://127.0.0.1:8000'

export interface ResumeUploadResponse {
  analysis_id: string
  filename: string
  skills: string[]
}

export interface AIAnalysis {
  overall_assessment: string
  strengths: string[]
  weaknesses: string[]
  suggestions: string[]
}

export interface JobMatchResponse {
  analysis_id: string
  required_skills: string[]
  matched_skills: string[]
  missing_skills: string[]
  match_score: number
  ai_analysis: AIAnalysis
}

async function getErrorMessage(response: Response): Promise<string> {
  try {
    const data = await response.json()
    return data.detail ?? 'Something went wrong. Please try again.'
  } catch {
    return 'Something went wrong. Please try again.'
  }
}

export async function uploadResume(
  file: File,
): Promise<ResumeUploadResponse> {
  const formData = new FormData()
  formData.append('file', file)

  const response = await fetch(`${API_BASE_URL}/resume/upload`, {
    method: 'POST',
    body: formData,
  })

  if (!response.ok) {
    throw new Error(await getErrorMessage(response))
  }

  return response.json()
}

export async function matchJob(
  analysisId: string,
  jobDescription: string,
): Promise<JobMatchResponse> {
  const response = await fetch(`${API_BASE_URL}/job/match`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      analysis_id: analysisId,
      text: jobDescription,
    }),
  })

  if (!response.ok) {
    throw new Error(await getErrorMessage(response))
  }

  return response.json()
}