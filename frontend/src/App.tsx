
import { useState } from 'react'
import {
  uploadResume,
  matchJob,
  analyzeResumeQuality,
} from './services/api'

import type {
  JobMatchResponse,
  ResumeQualityAnalysis,
} from './services/api'

import './App.css'

function App() {
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<JobMatchResponse | null>(null)
  const [theme, setTheme] = useState<'dark' | 'light'>(() => {
    const savedTheme = localStorage.getItem('resume-orbit-theme')
    return savedTheme === 'light' ? 'light' : 'dark'
  })

  const [analysisId, setAnalysisId] = useState<string | null>(null)
  const [qualityResult, setQualityResult] =
    useState<ResumeQualityAnalysis | null>(null)
  const [qualityLoading, setQualityLoading] = useState(false)

  const [resume, setResume] = useState<File | null>(null)
  const [jobDescription, setJobDescription] = useState('')
  const [message, setMessage] = useState('')

  function toggleTheme() {
    const nextTheme = theme === 'dark' ? 'light' : 'dark'
    setTheme(nextTheme)
    localStorage.setItem('resume-orbit-theme', nextTheme)
  }



  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()

    if (!resume) {
      setMessage('Please upload your resume first.')
      return
    }

    if (!jobDescription.trim()) {
      setMessage('Please enter a job description.')
      return
    }

    setLoading(true)
    setMessage('')
    setResult(null)

    try {
      let currentAnalysisId = analysisId

      if (!currentAnalysisId) {
        const uploaded = await uploadResume(resume)
        currentAnalysisId = uploaded.analysis_id
        setAnalysisId(currentAnalysisId)
      }

      const match = await matchJob(currentAnalysisId, jobDescription)

      setResult(match)
      setMessage('Job matching completed successfully.')
    } catch (error) {
      setMessage(
        error instanceof Error
          ? error.message
          : 'Unable to analyze your resume. Please try again.',
      )
    } finally {
      setLoading(false)
    }
  }


  async function handleQualityAnalysis() {
    if (!resume) {
      setMessage('Please upload your resume first.')
      return
    }

    setQualityLoading(true)
    setMessage('')
    setQualityResult(null)

    try {
      let currentAnalysisId = analysisId

      if (!currentAnalysisId) {
        const uploaded = await uploadResume(resume)
        currentAnalysisId = uploaded.analysis_id
        setAnalysisId(currentAnalysisId)
      }

      const response = await analyzeResumeQuality(currentAnalysisId)

      setQualityResult(response.quality_analysis)
      setMessage('Resume quality and ATS analysis completed.')
    } catch (error) {
      setMessage(
        error instanceof Error
          ? error.message
          : 'Unable to analyze resume quality. Please try again.',
      )
    } finally {
      setQualityLoading(false)
    }
  }

  return (
    <div className={`app ${theme}`}>
      <div className="ambient ambient-one" />
      <div className="ambient ambient-two" />

      <header className="navbar">
        <a className="brand" href="#home">
          <span className="brand-icon">
            <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
              <circle cx="12" cy="12" r="3" />
              <ellipse cx="12" cy="12" rx="10" ry="4.5" transform="rotate(-35 12 12)" />
              <path d="M18.5 4.5h.01" />
            </svg>
          </span>
          <span>
            Resume<span className="brand-accent">Orbit</span>
          </span>
        </a>

        <nav className="nav-links" aria-label="Main navigation">
          <a href="#analyzer">Analyzer</a>
          <a href="#how-it-works">How it works</a>
        </nav>

        <button
          className="theme-toggle"
          onClick={toggleTheme}
          type="button"
          aria-label={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
        >
          <span>{theme === 'dark' ? '☀' : '☾'}</span>
          <span className="theme-label">
            {theme === 'dark' ? 'Light mode' : 'Dark mode'}
          </span>
        </button>
      </header>

      <main id="home">
        <section className="hero">
          <div className="eyebrow">
            <span className="status-dot" />
            YOUR NEXT CAREER MOVE STARTS HERE
          </div>

          <h1>
            Your experience.
            <br />
            <span className="gradient-text">Your next orbit.</span>
          </h1>

          <p className="hero-description">
            Discover how well your resume aligns with your dream role.
            Get useful insights, identify skill gaps, and move forward
            with confidence.
          </p>

          <a className="hero-link" href="#analyzer">
            Analyze your resume <span>↓</span>
          </a>

          <div className="orbit-decoration" aria-hidden="true">
            <div className="orbit-ring ring-one" />
            <div className="orbit-ring ring-two" />
            <div className="orbit-core">
              <svg viewBox="0 0 24 24" fill="none">
                <path d="M7 4.5h7l4 4V20H7z" />
                <path d="M14 4.5V9h4M10 13h5M10 16h5" />
              </svg>
            </div>
            <span className="orbit-star star-one">✦</span>
            <span className="orbit-star star-two">✧</span>
            <span className="orbit-star star-three">·</span>
          </div>
        </section>

        <section className="analyzer-section" id="analyzer">
          <div className="section-heading">
            <span className="section-kicker">THE ANALYSIS STATION</span>
            <h2>Let's find your match.</h2>
            <p>Start with your resume and the role you're aiming for.</p>
          </div>

          <form className="analyzer-card" onSubmit={handleSubmit}>
            <div className="card-heading">
              <div>
                <span className="step-label">STEP 01</span>
                <h3>Upload your resume</h3>
                <p>Give us a snapshot of your experience.</p>
              </div>
              <span className="step-number">01</span>
            </div>

            <label className="upload-area">
              <input
                type="file"
                accept=".pdf,.docx"
                onChange={(event) => {
                  setResume(event.target.files?.[0] ?? null)
                  setAnalysisId(null)
                  setQualityResult(null)
                  setResult(null)
                  setMessage('')
                }}
              />
              <span className="upload-icon">
                <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
                  <path d="M12 16V4m0 0L7.5 8.5M12 4l4.5 4.5" />
                  <path d="M5 14v5h14v-5" />
                </svg>
              </span>
              <strong>
                {resume ? resume.name : 'Drop your resume into orbit'}
              </strong>
              <span className="upload-hint">
                {resume
                  ? `${(resume.size / 1024 / 1024).toFixed(2)} MB · Selected`
                  : 'or click to browse your files'}
              </span>
              <span className="file-types">PDF or DOCX · Maximum 5 MB</span>
            </label>


            <button
              className="analyze-button quality-button"
              type="button"
              onClick={handleQualityAnalysis}
              disabled={loading || qualityLoading}
            >
              {qualityLoading ? 'Analyzing resume...' : 'Check resume quality & ATS'}
              <span>{qualityLoading ? '◌' : '↗'}</span>
            </button>

            <div className="form-divider">
              <span />
              <span className="divider-orbit">✦</span>
              <span />
            </div>

            <div className="card-heading job-heading">
              <div>
                <span className="step-label">STEP 02</span>
                <h3>Set your destination</h3>
                <p>Paste the job description you want to target.</p>
              </div>
              <span className="step-number">02</span>
            </div>

            <label className="textarea-label" htmlFor="job-description">
              JOB DESCRIPTION
            </label>
            <textarea
              id="job-description"
              value={jobDescription}
              onChange={(event) => {
                setJobDescription(event.target.value)
                setMessage('')
              }}
              placeholder="Paste the role, responsibilities, and qualifications here..."
              rows={7}
            />

            <div className="form-footer">
              <span className="privacy-note">
                <span>✧</span> Your career journey, one step at a time.
              </span>
              <button
                className="analyze-button"
                type="submit"
                disabled={loading}
              >
                {loading ? 'Analyzing...' : 'Analyze my resume'}
                <span>{loading ? '◌' : '↗'}</span>
              </button>
            </div>

            {message && (
              <p className="form-message" role="status">
                {message}
              </p>
            )}



            {result && (
              <section className="results-panel" aria-live="polite">
                <div className="results-heading">
                  <span className="section-kicker">YOUR RESULTS</span>
                  <h3>Here's your career alignment.</h3>
                  <p>{result.ai_analysis.overall_assessment}</p>
                </div>

                <div className="score-card">
                  <span className="score-label">REQUIREMENT MATCH</span>

                  <strong className="score-value">
                    {result.match_score === null
                      ? 'N/A'
                      : `${result.match_score}%`}
                  </strong>

                  <div
                    className="score-track"
                    role="progressbar"
                    aria-label="Weighted requirement coverage"
                    aria-valuemin={0}
                    aria-valuemax={100}
                    aria-valuenow={result.match_score ?? undefined}
                  >
                    <div
                      className="score-fill"
                      style={{
                        width: `${result.match_score ?? 0}%`,
                      }}
                    />
                  </div>

                  <span className="score-caption">
                    {result.match_score === null
                      ? 'Not enough identifiable requirements to calculate a score.'
                      : 'Weighted coverage of the job requirements identified by AI.'}
                  </span>

                  <div className="requirement-summary">
                    <span>
                      <strong>
                        {result.ai_analysis.requirement_assessments.filter(
                          (item) => item.status === 'supported',
                        ).length}
                      </strong>
                      {' '}fully supported
                    </span>

                    <span>
                      <strong>
                        {result.ai_analysis.requirement_assessments.filter(
                          (item) => item.status === 'partial',
                        ).length}
                      </strong>
                      {' '}partial
                    </span>

                    <span>
                      <strong>
                        {result.ai_analysis.requirement_assessments.filter(
                          (item) => item.status === 'not_found',
                        ).length}
                      </strong>
                      {' '}without evidence
                    </span>
                  </div>
                </div>

                <div className="skills-grid">
                  <div className="result-card">
                    <h4>Strengths aligned with the role</h4>

                    {result.matched_skills.length ? (
                      <ul>
                        {result.matched_skills.map((skill) => (
                          <li key={skill}>{skill}</li>
                        ))}
                      </ul>
                    ) : (
                      <p>No requirements were fully supported by the current assessment.</p>
                    )}
                  </div>

                  <div className="result-card">
                    <h4>Requirements needing attention</h4>

                    {result.missing_skills.length ? (
                      <ul>
                        {result.missing_skills.map((skill) => (
                          <li key={skill}>{skill}</li>
                        ))}
                      </ul>
                    ) : (
                      <p>No unsupported or partially supported requirements detected.</p>
                    )}
                  </div>
                </div>

                <div className="result-card requirement-section">
                  <h4>Job requirement breakdown</h4>
                  <p>
                    Review how each requirement was evaluated and what evidence
                    the AI found in your resume.
                  </p>

                  {result.ai_analysis.requirement_assessments.length ? (
                    <div className="requirement-list">
                      {result.ai_analysis.requirement_assessments.map(
                        (item, index) => (
                          <article
                            className="requirement-item"
                            key={`${item.title}-${index}`}
                          >
                            <div className="requirement-item-heading">
                              <div>
                                <h5>{item.title}</h5>
                                <span className="requirement-importance">
                                  {item.importance === 'required'
                                    ? 'Required'
                                    : 'Preferred'}
                                </span>
                              </div>

                              <span
                                className={`requirement-status status-${item.status}`}
                              >
                                {item.status === 'supported'
                                  ? 'Supported'
                                  : item.status === 'partial'
                                    ? 'Partially supported'
                                    : 'No evidence found'}
                              </span>
                            </div>

                            <p>
                              <strong>Resume evidence:</strong> {item.evidence}
                            </p>

                            <p>
                              <strong>Assessment:</strong> {item.explanation}
                            </p>
                          </article>
                        ),
                      )}
                    </div>
                  ) : (
                    <p>
                      The job description did not provide enough information to
                      identify reliable requirements. Try adding responsibilities,
                      qualifications, or details about the role.
                    </p>
                  )}
                </div>

                <div className="result-card ai-feedback">
                  <h4>What you're already doing well</h4>
                  <ul>
                    {result.ai_analysis.strengths.map((item, index) => (
                      <li key={`${index}-${item}`}>{item}</li>
                    ))}
                  </ul>

                  <h4>Areas to improve</h4>
                  <ul>
                    {result.ai_analysis.weaknesses.map((item, index) => (
                      <li key={`${index}-${item}`}>{item}</li>
                    ))}
                  </ul>

                  <h4>Your next steps</h4>
                  <ul>
                    {result.ai_analysis.suggestions.map((item, index) => (
                      <li key={`${index}-${item}`}>{item}</li>
                    ))}
                  </ul>
                </div>
              </section>
            )}


            {qualityResult && (
              <section className="results-panel quality-results" aria-live="polite">
                <div className="results-heading">
                  <span className="section-kicker">RESUME HEALTH CHECK</span>
                  <h3>Your resume, reviewed.</h3>
                  <p>{qualityResult.summary}</p>
                </div>

                <div className="skills-grid">
                  <div className="score-card">
                    <span className="score-label">RESUME QUALITY</span>
                    <strong className="score-value">
                      {qualityResult.overall_score}/100
                    </strong>
                    <div
                      className="score-track"
                      role="progressbar"
                      aria-label="Resume quality score"
                      aria-valuemin={0}
                      aria-valuemax={100}
                      aria-valuenow={qualityResult.overall_score}
                    >
                      <div
                        className="score-fill"
                        style={{ width: `${qualityResult.overall_score}%` }}
                      />
                    </div>
                    <span className="score-caption">
                      Clarity, structure, achievements and completeness
                    </span>
                  </div>

                  <div className="score-card">
                    <span className="score-label">ATS FRIENDLINESS</span>
                    <strong className="score-value">
                      {qualityResult.ats_score}/100
                    </strong>
                    <div
                      className="score-track"
                      role="progressbar"
                      aria-label="ATS friendliness score"
                      aria-valuemin={0}
                      aria-valuemax={100}
                      aria-valuenow={qualityResult.ats_score}
                    >
                      <div
                        className="score-fill"
                        style={{ width: `${qualityResult.ats_score}%` }}
                      />
                    </div>
                    <span className="score-caption">
                      Text structure, recognizable sections and parsing signals
                    </span>
                  </div>
                </div>

                <div className="result-card requirement-section">
                  <h4>Resume strengths</h4>
                  {qualityResult.strengths.length ? (
                    <ul>
                      {qualityResult.strengths.map((item, index) => (
                        <li key={index}>{item}</li>
                      ))}
                    </ul>
                  ) : (
                    <p>No clear strengths could be identified from the extracted text.</p>
                  )}

                  <h4>Priority improvements</h4>
                  {qualityResult.improvements.length ? (
                    <ul>
                      {qualityResult.improvements.map((item, index) => (
                        <li key={index}>{item}</li>
                      ))}
                    </ul>
                  ) : (
                    <p>No major improvements were identified.</p>
                  )}
                </div>

                <div className="result-card requirement-section">
                  <h4>ATS assessment</h4>
                  <p>{qualityResult.ats_summary}</p>

                  <h4>What is already working</h4>
                  <ul>
                    {qualityResult.ats_strengths.map((item, index) => (
                      <li key={index}>{item}</li>
                    ))}
                  </ul>

                  <h4>Potential ATS issues</h4>
                  {qualityResult.ats_issues.length ? (
                    <ul>
                      {qualityResult.ats_issues.map((item, index) => (
                        <li key={index}>{item}</li>
                      ))}
                    </ul>
                  ) : (
                    <p>No clear ATS concerns were identified in the extracted text.</p>
                  )}

                  <h4>How to improve ATS readiness</h4>
                  <ul>
                    {qualityResult.ats_improvements.map((item, index) => (
                      <li key={index}>{item}</li>
                    ))}
                  </ul>
                </div>

                <div className="result-card requirement-section">
                  <h4>Section-by-section review</h4>
                  <div className="requirement-list">
                    {qualityResult.section_reviews.map((item, index) => (
                      <article className="requirement-item" key={`${item.section}-${index}`}>
                        <div className="requirement-item-heading">
                          <h5>{item.section}</h5>
                          <span className="requirement-status status-partial">
                            {item.status}
                          </span>
                        </div>
                        <p>{item.feedback}</p>
                      </article>
                    ))}
                  </div>

                  <h4>Missing or unclear information</h4>
                  {qualityResult.missing_information.length ? (
                    <ul>
                      {qualityResult.missing_information.map((item, index) => (
                        <li key={index}>{item}</li>
                      ))}
                    </ul>
                  ) : (
                    <p>No important missing information was identified.</p>
                  )}

                  <h4>Achievement writing tips</h4>
                  {qualityResult.achievement_feedback.length ? (
                    <ul>
                      {qualityResult.achievement_feedback.map((item, index) => (
                        <li key={index}>{item}</li>
                      ))}
                    </ul>
                  ) : (
                    <p>No specific achievement-writing changes were identified.</p>
                  )}
                </div>

                <p className="score-caption">
                  These scores are AI-generated guidance, not a guarantee of ATS
                  acceptance. Visual layout and formatting cannot be fully verified
                  from extracted text alone.
                </p>
              </section>
            )}
            
          </form>
        </section>

        <section className="how-section" id="how-it-works">
          <div className="section-heading">
            <span className="section-kicker">A CLEARER CAREER PATH</span>
            <h2>Three steps. More direction.</h2>
          </div>

          <div className="feature-grid">
            <article className="feature-card">
              <span className="feature-icon">↗</span>
              <span className="feature-index">01 / UPLOAD</span>
              <h3>Bring your story</h3>
              <p>Share your resume to identify the skills and experience already in your corner.</p>
            </article>

            <article className="feature-card">
              <span className="feature-icon">◎</span>
              <span className="feature-index">02 / COMPARE</span>
              <h3>Find your alignment</h3>
              <p>Compare your current skills with the requirements of your target position.</p>
            </article>

            <article className="feature-card">
              <span className="feature-icon">✧</span>
              <span className="feature-index">03 / IMPROVE</span>
              <h3>Move with purpose</h3>
              <p>Use practical feedback to spot gaps and strengthen your next application.</p>
            </article>
          </div>
        </section>
      </main>

      <footer className="footer">
        <a className="brand footer-brand" href="#home">
          <span className="brand-icon">
            <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
              <circle cx="12" cy="12" r="3" />
              <ellipse cx="12" cy="12" rx="10" ry="4.5" transform="rotate(-35 12 12)" />
            </svg>
          </span>
          <span>
            Resume<span className="brand-accent">Orbit</span>
          </span>
        </a>
        <p>Made for the next chapter of your career.</p>
      </footer>
    </div>
  )
}

export default App