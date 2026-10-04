'use client';

import { useEffect, useRef, useState } from 'react';
import Link from 'next/link';
import { hasToken, resumes, type Resume } from '@/lib/api';
import { Topbar } from '@/components/Topbar';
import { Sidebar } from '@/components/Sidebar';
import { useAuth } from '@/lib/auth-context';
import {
  FileText,
  UploadCloud,
  Sparkles,
  Download,
  Mail,
  Briefcase,
  Calendar,
  CheckCircle2,
  Clock,
  Code,
  Layers,
  ArrowRight,
} from 'lucide-react';

export default function ResumesPage() {
  const { user } = useAuth();
  const [myResumes, setMyResumes] = useState<Resume[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    async function loadResumes() {
      if (!hasToken()) {
        setMyResumes([]);
        setLoading(false);
        return;
      }
      try {
        const list = await resumes.list();
        setMyResumes(list);
      } catch {
        // Not logged in
      } finally {
        setLoading(false);
      }
    }
    loadResumes();
  }, [user]);

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploading(true);
    try {
      const result = await resumes.upload(file);
      setMyResumes((prev) => [result.resume, ...prev]);
    } catch (err) {
      console.error('Upload failed:', err);
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="app-shell">
      <Topbar />
      <Sidebar />

      <main className="main-content">
        {/* Ambient Dark Luxury Orb */}
        <div className="hero-orb" />

        <div className="page-header">
          <div>
            <div className="page-badge">
              <span>DOCUMENT REPOSITORY</span>
            </div>
            <h1 className="page-title" style={{ marginTop: '6px' }}>
              Master Resumes & Parsed Profiles
            </h1>
            <p className="page-subtitle">
              Upload PDF/DOCX resumes for structured JSON parsing, ATS scoring, and LaTeX export.
            </p>
          </div>
          <div>
            <input
              ref={fileRef}
              type="file"
              accept=".pdf,.docx"
              onChange={handleUpload}
              style={{ display: 'none' }}
            />
            <button
              className="btn btn-primary"
              onClick={() => fileRef.current?.click()}
              disabled={uploading}
            >
              <UploadCloud size={16} />
              <span>{uploading ? 'Parsing with AI...' : 'Upload Master Resume'}</span>
            </button>
          </div>
        </div>

        {/* Upload Drop Area Banner (Dark Luxury) */}
        <div
          role="button"
          tabIndex={0}
          onClick={() => fileRef.current?.click()}
          onKeyDown={(e) => {
            if (e.key === 'Enter' || e.key === ' ') {
              e.preventDefault();
              fileRef.current?.click();
            }
          }}
          style={{
            border: '1px dashed var(--border-medium)',
            background: 'var(--bg-card)',
            boxShadow: 'inset 0 1px 0 rgba(255, 248, 230, 0.08), 0 4px 24px rgba(0, 0, 0, 0.45)',
            borderRadius: 'var(--r-lg)',
            padding: '36px 24px',
            textAlign: 'center',
            cursor: 'pointer',
            marginBottom: '32px',
            transition: 'border-color var(--dur-base) ease',
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.borderColor = 'var(--accent)';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.borderColor = 'var(--border-medium)';
          }}
        >
          <div
            style={{
              width: '52px',
              height: '52px',
              borderRadius: 'var(--r-md)',
              background: 'var(--accent-subtle)',
              border: '1px solid var(--border-subtle)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'var(--accent)',
              margin: '0 auto 14px',
            }}
          >
            <UploadCloud size={24} />
          </div>
          <h2 style={{ fontSize: '1.15rem', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '6px' }}>
            Click or drag & drop to upload new resume
          </h2>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
            Supports PDF, DOCX up to 10MB &middot; Automated section parser & keyword extraction
          </p>
        </div>

        {loading ? (
          <div style={{ textAlign: 'center', padding: '60px', color: 'var(--text-muted)' }}>
            <div
              style={{
                display: 'inline-block',
                width: '36px',
                height: '36px',
                border: '3px solid var(--border-medium)',
                borderTopColor: 'var(--accent)',
                borderRadius: '50%',
                animation: 'spin 0.8s linear infinite',
                marginBottom: '16px',
              }}
            />
            <p style={{ fontWeight: 600, color: 'var(--text-primary)' }}>Loading stored resumes...</p>
          </div>
        ) : myResumes.length === 0 ? (
          <div className="card" style={{ textAlign: 'center', padding: '60px 40px' }}>
            <FileText size={48} style={{ opacity: 0.3, marginBottom: '16px' }} />
            <h2 style={{ fontSize: '1.3rem', fontWeight: 700, marginBottom: '8px', color: 'var(--text-primary)' }}>
              No resumes cataloged yet
            </h2>
            <p style={{ color: 'var(--text-muted)', maxWidth: '420px', margin: '0 auto 24px' }}>
              Upload your master CV to unlock automated STAR bullet tailoring, ATS keyword alignment, and 1-click tailored PDF exports.
            </p>
            <button
              className="btn btn-primary"
              onClick={() => fileRef.current?.click()}
            >
              <UploadCloud size={16} />
              <span>Select File to Upload</span>
            </button>
          </div>
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(360px, 1fr))', gap: '20px' }}>
            {myResumes.map((r) => {
              const contact = (r.content as Record<string, unknown>)?.contact as Record<string, string> | undefined;
              const skills = (r.content as Record<string, unknown>)?.skills as string[] | undefined;
              const expCount = ((r.content as Record<string, unknown>)?.workExperience as unknown[])?.length ?? 0;

              return (
                <div key={r.id} className="card" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
                  <div>
                    <div className="card-header">
                      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                        <div
                          style={{
                            width: '38px',
                            height: '38px',
                            borderRadius: 'var(--r-sm)',
                            background: r.is_master
                              ? 'var(--accent-subtle)'
                              : 'rgba(255, 248, 230, 0.05)',
                            border: '1px solid var(--border-subtle)',
                            color: r.is_master ? 'var(--accent)' : 'var(--text-secondary)',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                          }}
                        >
                          <FileText size={18} />
                        </div>
                        <div>
                          <div className="card-title" style={{ fontSize: '1.05rem' }}>
                            {r.filename || 'Master_Resume.pdf'}
                          </div>
                          <div style={{ display: 'flex', gap: '6px', marginTop: '3px' }}>
                            {r.is_master && (
                              <span className="badge badge-warning" style={{ fontSize: '0.68rem' }}>
                                Master Profile
                              </span>
                            )}
                            {r.is_default && (
                              <span className="badge badge-info" style={{ fontSize: '0.68rem' }}>
                                Default
                              </span>
                            )}
                          </div>
                        </div>
                      </div>

                      <span
                        className={`badge ${r.processing_status === 'done' ? 'badge-success' : 'badge-warning'}`}
                        style={{ textTransform: 'capitalize' }}
                      >
                        {r.processing_status === 'done' ? <CheckCircle2 size={12} /> : <Clock size={12} />}
                        <span>{r.processing_status}</span>
                      </span>
                    </div>

                    {/* Candidate Details */}
                    <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', margin: '14px 0' }}>
                      {contact?.name && (
                        <p style={{ fontWeight: 700, color: 'var(--text-primary)', fontSize: '0.95rem', marginBottom: '4px' }}>
                          {contact.name}
                        </p>
                      )}
                      {contact?.email && (
                        <p style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '4px' }}>
                          <Mail size={13} style={{ color: 'var(--text-muted)' }} />
                          <span>{contact.email}</span>
                        </p>
                      )}
                      <p style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '10px' }}>
                        <Briefcase size={13} style={{ color: 'var(--text-muted)' }} />
                        <span>{expCount} structured experience entries</span>
                      </p>

                      {skills && skills.length > 0 && (
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', marginTop: '10px' }}>
                          {skills.slice(0, 8).map((s) => (
                            <span
                              key={s}
                              className="badge badge-neutral"
                              style={{
                                fontSize: '0.72rem',
                                background: 'rgba(255, 255, 255, 0.05)',
                              }}
                            >
                              {s}
                            </span>
                          ))}
                          {skills.length > 8 && (
                            <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', alignSelf: 'center' }}>
                              +{skills.length - 8} more
                            </span>
                          )}
                        </div>
                      )}
                    </div>
                  </div>

                  <div>
                    {/* Action Buttons */}
                    <div style={{ display: 'flex', gap: '8px', marginTop: '16px', flexWrap: 'wrap' }}>
                      <button
                        className="btn btn-secondary btn-sm"
                        style={{ flex: 1 }}
                        onClick={async () => {
                          const token = localStorage.getItem('jobforge_token');
                          const res = await fetch(resumes.pdfUrl(r.id), {
                            headers: token ? { Authorization: `Bearer ${token}` } : {},
                          });
                          if (!res.ok) {
                            alert('Could not generate ATS PDF');
                            return;
                          }
                          const blob = await res.blob();
                          const a = document.createElement('a');
                          a.href = window.URL.createObjectURL(blob);
                          a.download = `${r.filename || 'Resume'}.pdf`;
                          a.click();
                        }}
                      >
                        <Download size={14} />
                        <span>ATS PDF</span>
                      </button>

                      <button
                        className="btn btn-secondary btn-sm"
                        style={{ flex: 1 }}
                        onClick={async () => {
                          const token = localStorage.getItem('jobforge_token');
                          const res = await fetch(resumes.latexPdfUrl(r.id), {
                            headers: token ? { Authorization: `Bearer ${token}` } : {},
                          });
                          if (!res.ok) {
                            alert('Could not generate LaTeX');
                            return;
                          }
                          const contentType = res.headers.get('content-type') || '';
                          const blob = await res.blob();
                          const a = document.createElement('a');
                          a.href = window.URL.createObjectURL(blob);
                          const ext = contentType.includes('pdf') ? 'pdf' : 'tex';
                          a.download = `${r.filename || 'Resume'}_latex.${ext}`;
                          a.click();
                        }}
                      >
                        <Code size={14} />
                        <span>LaTeX ({r.is_master ? 'Print' : '.tex'})</span>
                      </button>

                      <Link
                        href="/tailor"
                        className="btn btn-primary btn-sm"
                        style={{ width: '100%', marginTop: '4px' }}
                      >
                        <Sparkles size={14} />
                        <span>Tailor for Job Opening</span>
                      </Link>
                    </div>

                    <div
                      style={{
                        fontSize: '0.74rem',
                        color: 'var(--text-muted)',
                        marginTop: '14px',
                        borderTop: '1px solid var(--border-subtle)',
                        paddingTop: '8px',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '4px',
                      }}
                    >
                      <Calendar size={12} />
                      <span>Uploaded {new Date(r.created_at).toLocaleDateString()}</span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </main>
    </div>
  );
}
