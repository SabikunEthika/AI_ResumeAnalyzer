
const API_BASE_URL = (
  import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'
).replace(/\/$/, '')

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

export interface AnalyzeResponse {
  filename: string
  skills: string[]
  job_match: JobMatchResponse | null
  quality_analysis: ResumeQualityAnalysis | null
}

async function getErrorMessage(response: Response): Promise<string> {
  try {
    const data = await response.json()

    if (typeof data.detail === 'string') {
      return data.detail
    }

    if (Array.isArray(data.detail)) {
      return data.detail
        .map((error: { msg?: string }) => error.msg ?? 'Invalid request')
        .join('. ')
    }

    return 'Something went wrong. Please try again.'
  } catch {
    return 'Something went wrong. Please try again.'
  }
}

async function analyzeResume(
  file: File,
  options: {
    jobDescription?: string
    includeQuality?: boolean
  },
): Promise<AnalyzeResponse> {
  const formData = new FormData()

  formData.append('file', file)
  formData.append(
    'include_quality',
    String(options.includeQuality ?? false),
  )

  if (options.jobDescription?.trim()) {
    formData.append('job_description', options.jobDescription.trim())
  }

  let response: Response

  try {
    response = await fetch(`${API_BASE_URL}/analyze`, {
      method: 'POST',
      body: formData,
    })
  } catch {
    throw new Error(
      'Cannot connect to ResumeOrbit. Please make sure the backend server is running.',
    )
  }

  if (!response.ok) {
    throw new Error(await getErrorMessage(response))
  }

  return response.json()
}

export async function matchJob(
  file: File,
  jobDescription: string,
): Promise<JobMatchResponse> {
  if (!jobDescription.trim()) {
    throw new Error('Please enter a job description.')
  }

  const data = await analyzeResume(file, {
    jobDescription,
    includeQuality: false,
  })

  if (!data.job_match) {
    throw new Error('Job matching did not return a result. Please try again.')
  }

  return data.job_match
}

export async function analyzeResumeQuality(
  file: File,
): Promise<ResumeQualityAnalysis> {
  const data = await analyzeResume(file, {
    includeQuality: true,
  })

  if (!data.quality_analysis) {
    throw new Error(
      'Resume quality analysis did not return a result. Please try again.',
    )
  }

  return data.quality_analysis
}
