
import { jsPDF } from 'jspdf'

import type {
  JobMatchResponse,
  ResumeQualityAnalysis,
} from './api'

interface PdfReportOptions {
  filename: string
  jobMatch?: JobMatchResponse | null
  qualityAnalysis?: ResumeQualityAnalysis | null
}

export function downloadAnalysisReport({
  filename,
  jobMatch,
  qualityAnalysis,
}: PdfReportOptions): void {
  if (!jobMatch && !qualityAnalysis) {
    throw new Error('There are no completed analyses to download.')
  }

  const pdf = new jsPDF({
    orientation: 'portrait',
    unit: 'mm',
    format: 'a4',
  })

  const pageWidth = pdf.internal.pageSize.getWidth()
  const pageHeight = pdf.internal.pageSize.getHeight()
  const margin = 18
  const contentWidth = pageWidth - margin * 2
  let y = 20

  function ensureSpace(requiredHeight = 10) {
    if (y + requiredHeight > pageHeight - 18) {
      pdf.addPage()
      y = 20
    }
  }

  function addTitle(text: string) {
    ensureSpace(12)
    pdf.setFont('helvetica', 'bold')
    pdf.setFontSize(15)
    pdf.text(text, margin, y)
    y += 9
  }

  function addParagraph(text: string) {
    if (!text.trim()) return

    pdf.setFont('helvetica', 'normal')
    pdf.setFontSize(10)

    const lines = pdf.splitTextToSize(text, contentWidth)
    const lineHeight = 5
    let offset = 0

    while (offset < lines.length) {
      ensureSpace(lineHeight)

      const availableLines = Math.max(
        1,
        Math.floor((pageHeight - 18 - y) / lineHeight),
      )

      const chunk = lines.slice(offset, offset + availableLines)

      pdf.text(chunk, margin, y)
      y += chunk.length * lineHeight
      offset += chunk.length

      if (offset < lines.length) {
        pdf.addPage()
        y = 20
      }
    }

    y += 2
  }

  function addSection(title: string, items: string[]) {
    if (items.length === 0) return

    addTitle(title)

    for (const item of items) {
      addParagraph(`• ${item}`)
    }

    y += 2
  }

  function addScore(label: string, score: number | null | undefined) {
    if (score === null || score === undefined) return
    addParagraph(`${label}: ${score}/100`)
  }

  pdf.setFont('helvetica', 'bold')
  pdf.setFontSize(23)
  pdf.text('ResumeOrbit', margin, y)
  y += 9

  pdf.setFont('helvetica', 'normal')
  pdf.setFontSize(11)
  pdf.text('Resume Analysis Report', margin, y)
  y += 7

  pdf.setFontSize(9)
  pdf.text(`Resume: ${filename}`, margin, y)
  y += 5
  pdf.text(`Generated: ${new Date().toLocaleDateString()}`, margin, y)
  y += 10

  if (jobMatch) {
    addTitle('Job Match Analysis')

    addScore('Match score', jobMatch.match_score)

    addParagraph(jobMatch.ai_analysis.overall_assessment)

    addSection('Matched skills', jobMatch.matched_skills)
    addSection('Missing skills', jobMatch.missing_skills)
    addSection('Required skills', jobMatch.required_skills)

    addSection('Strengths', jobMatch.ai_analysis.strengths)
    addSection('Weaknesses', jobMatch.ai_analysis.weaknesses)
    addSection('Suggestions', jobMatch.ai_analysis.suggestions)

    if (jobMatch.ai_analysis.requirement_assessments.length > 0) {
      addTitle('Requirement Assessments')

      for (const requirement of jobMatch.ai_analysis.requirement_assessments) {
        addParagraph(
          `${requirement.title} (${requirement.importance}) — ${requirement.status}`,
        )
        addParagraph(`Evidence: ${requirement.evidence}`)
        addParagraph(`Explanation: ${requirement.explanation}`)
      }
    }
  }

  if (qualityAnalysis) {
    addTitle('Resume Quality Analysis')

    addScore('Overall resume score', qualityAnalysis.overall_score)
    addParagraph(qualityAnalysis.summary)

    addSection('Resume strengths', qualityAnalysis.strengths)
    addSection('Areas for improvement', qualityAnalysis.improvements)

    addTitle('ATS Analysis')
    addScore('ATS score', qualityAnalysis.ats_score)
    addParagraph(qualityAnalysis.ats_summary)

    addSection('ATS strengths', qualityAnalysis.ats_strengths)
    addSection('ATS issues', qualityAnalysis.ats_issues)
    addSection('ATS improvements', qualityAnalysis.ats_improvements)

    if (qualityAnalysis.section_reviews.length > 0) {
      addTitle('Section Reviews')

      for (const review of qualityAnalysis.section_reviews) {
        addParagraph(`${review.section} — ${review.status}`)
        addParagraph(review.feedback)
      }
    }

    addSection('Missing Information', qualityAnalysis.missing_information)
    addSection('Achievement Feedback', qualityAnalysis.achievement_feedback)
  }

  ensureSpace(12)
  pdf.setFont('helvetica', 'italic')
  pdf.setFontSize(8)
  pdf.text(
    'This report is AI-generated and should be reviewed critically.',
    margin,
    y,
  )

  const safeFilename = filename
    .replace(/\.[^/.]+$/, '')
    .replace(/[^a-zA-Z0-9_-]+/g, '_')
    .slice(0, 80) || 'resume'

  pdf.save(`ResumeOrbit_${safeFilename}_Report.pdf`)
}
