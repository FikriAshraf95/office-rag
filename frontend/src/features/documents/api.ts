import { http } from '@/api/http'
import type { components } from '@/api/schema'
import documentsFixture from '@/fixtures/documents.json'

export type Document = components['schemas']['DocumentOut']
export type DocumentPatch = components['schemas']['DocumentPatch']
export type DocumentStatus = Document['status']
export type IngestStatus = Document['ingestStatus']
export type Chunk = components['schemas']['ChunkOut']

/** Details applied to an upload (SPEC-08 §4.1). Empty values are not sent. */
export interface UploadDetails {
  title?: string
  docType?: string
  department?: string
  effectiveDate?: string
  accessGroups?: string[]
}

const useFixtures = import.meta.env.VITE_USE_FIXTURES === '1'
const fixtureDocuments = documentsFixture.items as Document[]

export const documentsApi = {
  /** `GET /documents`: the documents the caller may see, newest first. */
  async list(): Promise<Document[]> {
    if (useFixtures) return fixtureDocuments
    return (await http.get<{ items: Document[] }>('/documents')).data.items
  },

  /** `GET /documents/{id}`: 404 for an unknown id or a document outside the caller's groups. */
  async get(id: string): Promise<Document> {
    if (useFixtures) {
      const found = fixtureDocuments.find((d) => d.id === id)
      if (found) return found
    }
    return (await http.get<Document>(`/documents/${id}`, { silent: true })).data
  },

  /** `POST /documents`: one file. Errors are shown per file by the caller, so they are not toasted. */
  async upload(
    file: File,
    details: UploadDetails,
    onProgress: (fraction: number) => void,
  ): Promise<Document> {
    const form = new FormData()
    form.append('file', file)
    if (details.title) form.append('title', details.title)
    if (details.docType) form.append('docType', details.docType)
    if (details.department) form.append('department', details.department)
    if (details.effectiveDate) form.append('effectiveDate', details.effectiveDate)
    for (const group of details.accessGroups ?? []) form.append('accessGroups', group)
    const response = await http.post<Document>('/documents', form, {
      silent: true,
      onUploadProgress: (e) => onProgress(e.total ? e.loaded / e.total : 0),
    })
    return response.data
  },

  /** `PATCH /documents/{id}`: send only the fields that change. */
  async patch(id: string, changes: DocumentPatch): Promise<Document> {
    return (await http.patch<Document>(`/documents/${id}`, changes)).data
  },

  /** `DELETE /documents/{id}`. */
  async remove(id: string): Promise<void> {
    await http.delete(`/documents/${id}`)
  },

  /** `POST /documents/{id}/reingest`: queue ingestion again. 409 `ingest_in_progress` while one is pending. */
  async reingest(id: string): Promise<Document> {
    return (await http.post<Document>(`/documents/${id}/reingest`)).data
  },

  /** `POST /documents/{id}/file`: replace the file (same id) and queue ingestion. 409 `ingest_in_progress` / `duplicate_document`. */
  async replaceFile(id: string, file: File): Promise<Document> {
    const form = new FormData()
    form.append('file', file)
    return (await http.post<Document>(`/documents/${id}/file`, form)).data
  },

  /** `GET /documents/{id}/chunks`: one page in order, with the total. */
  async chunks(id: string, offset: number, limit: number): Promise<{ items: Chunk[]; total: number }> {
    return (
      await http.get<{ items: Chunk[]; total: number }>(`/documents/${id}/chunks`, {
        params: { offset, limit },
        silent: true,
      })
    ).data
  },

  /** `GET /documents/{id}/chunks?around=`: the chunk and its neighbours, in order. Empty in fixtures mode. */
  async chunksAround(id: string, chunkId: string, radius = 1): Promise<Chunk[]> {
    if (useFixtures) return []
    return (
      await http.get<{ items: Chunk[]; total: number }>(`/documents/${id}/chunks`, {
        params: { around: chunkId, radius },
        silent: true,
      })
    ).data.items
  },

  /** `GET /documents/{id}/file` as a Blob. Fetched with `X-Demo-User`, never linked to directly (SPEC-07 §11 check 11). */
  async file(id: string): Promise<Blob> {
    return (await http.get<Blob>(`/documents/${id}/file`, { responseType: 'blob', silent: true })).data
  },
}

/** Saves a Blob under a file name through a temporary link. */
export function saveBlob(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  link.click()
  setTimeout(() => URL.revokeObjectURL(url), 10_000)
}
