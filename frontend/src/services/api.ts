
const API_BASE_URL = 'http://127.0.0.1:8000'

export interface ResumeUploadResponse {
  analysis_id: string
  filename: string
  skills: string[]
}

export interface RequirementAssessment {
  title: string
  importance: 'required' | 'preferred'
  status: 'supported' | 'partial' | 'not_found'
  evidence: string
  explanation: string
}

export interface AIAnalysis {
  overall_assessment: string
  strengths: string[]
  weaknesses: string[]
  suggestions: string[]
  requirement_assessments: RequirementAssessment[]
}

export interface JobMatchResponse {
  analysis_id: string
  required_skills: string[]
  matched_skills: string[]
  missing_skills: string[]
  match_score: number | null
  ai_analysis: AIAnalysis
}


export interface ResumeSectionReview {
  section: string
  status: string
  feedback: string
}

export interface ResumeQualityAnalysis {
  overall_score: number
  summary: string
  strengths: string[]
  improvements: string[]
  section_reviews: ResumeSectionReview[]
  missing_information: string[]
  achievement_feedback: string[]
  ats_score: number
  ats_summary: string
  ats_strengths: string[]
  ats_issues: string[]
  ats_improvements: string[]
}

export interface ResumeQualityResponse {
  analysis_id: string
  quality_analysis: ResumeQualityAnalysis
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


export async function analyzeResumeQuality(
  analysisId: string,
): Promise<ResumeQualityResponse> {
  const response = await fetch(`${API_BASE_URL}/resume/quality`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      analysis_id: analysisId,
    }),
  })

  if (!response.ok) {
    throw new Error(await getErrorMessage(response))
  }

  return response.json()
}