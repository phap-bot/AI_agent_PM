import { useState, useRef, useEffect } from 'react';
import { uploadDocumentsAsync, getIngestStatus } from '../lib/api';

export default function RequirementInputPanel({ onSubmit, isLoading, projectId }) {
  const [requirement, setRequirement] = useState('');
  const [nResults, setNResults] = useState(5);
  const [allowFallback, setAllowFallback] = useState(false);

  // Ingest states
  const [isIngesting, setIsIngesting] = useState(false);
  const [ingestData, setIngestData] = useState(null);  // IngestStatusResponse
  const [ingestError, setIngestError] = useState(null);
  const [jobId, setJobId] = useState(null);

  // Accumulated imported files across multiple uploads
  const [importedFiles, setImportedFiles] = useState([]);

  const fileInputRef = useRef(null);
  const pollingRef = useRef(null);

  // --- Polling logic ---
  useEffect(() => {
    if (!jobId || !isIngesting) return;

    console.log(`[POLL] Starting polling for job ${jobId}`);
    pollingRef.current = setInterval(async () => {
      try {
        console.log(`[POLL] Checking status for job ${jobId}...`);
        const status = await getIngestStatus(jobId);
        console.log(`[POLL] Status: ${status.status} - ${status.message}`);

        if (status.status === 'completed') {
          clearInterval(pollingRef.current);
          setIsIngesting(false);
          setIngestData(status);
          setJobId(null);

          // Accumulate newly imported files into the master list
          const newFiles = [
            ...(status.result?.indexed_files || []),
            ...(status.result?.skipped_files || []),
          ];
          setImportedFiles(prev => {
            const existing = new Set(prev.map(f => f.name));
            const additions = newFiles
              .filter(name => !existing.has(name))
              .map(name => ({ name, status: status.result?.indexed_files?.includes(name) ? 'new' : 'existing' }));
            return [...prev, ...additions];
          });

          console.log('[POLL] ✅ Ingestion completed!', status.result);
        } else if (status.status === 'failed') {
          clearInterval(pollingRef.current);
          setIsIngesting(false);
          setIngestError(status.message);
          setJobId(null);
          console.error('[POLL] ❌ Ingestion failed:', status.message);
        }
        // else: still "processing", keep polling
      } catch (err) {
        console.error('[POLL] Error polling status:', err);
      }
    }, 2000); // Poll every 2 seconds

    return () => {
      if (pollingRef.current) clearInterval(pollingRef.current);
    };
  }, [jobId, isIngesting]);

  const handleRemoveFile = (fileName) => {
    setImportedFiles(prev => prev.filter(f => f.name !== fileName));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (requirement.trim().length < 3) return;
    
    // Use accumulated imported files list
    const forcedDocs = importedFiles.map(f => f.name);

    onSubmit({
      requirement,
      n_results: parseInt(nResults, 10),
      allow_fallback_without_context: allowFallback,
      forced_context_docs: forcedDocs,
    });
  };

  const handleFileUpload = async (e) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;

    setIsIngesting(true);
    setIngestData(null);
    setIngestError(null);

    try {
      console.log(`[UPLOAD] Uploading ${files.length} file(s)...`);
      const jobResponse = await uploadDocumentsAsync(files, projectId);
      console.log(`[UPLOAD] Job created: ${jobResponse.job_id} - ${jobResponse.message}`);
      setJobId(jobResponse.job_id); // This triggers the polling useEffect
    } catch (err) {
      console.error('[UPLOAD] Upload failed:', err);
      setIsIngesting(false);
      setIngestError(err.message);
    } finally {
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  return (
    <section className="bg-white rounded-xl border border-outline-variant p-container-padding shadow-sm">
      <h2 className="font-headline-sm text-headline-sm text-primary mb-stack-md flex items-center gap-stack-sm">
        <span className="material-symbols-outlined">edit_note</span> Nhập yêu cầu từ khách hàng
      </h2>
      <div className="relative">
        <textarea 
          className="w-full h-40 bg-surface-container-lowest border border-outline-variant rounded-lg p-stack-md font-body-md text-on-surface focus:ring-2 focus:ring-primary focus:border-transparent outline-none transition-all resize-none" 
          placeholder="Dán email hoặc tin nhắn Slack vào đây..."
          value={requirement}
          onChange={(e) => setRequirement(e.target.value)}
          disabled={isLoading}
        />
      </div>

      <div className="mt-stack-md flex flex-col gap-stack-md">
        <div className="flex items-center gap-stack-sm">
          <input 
            type="file" 
            multiple 
            ref={fileInputRef}
            onChange={handleFileUpload} 
            className="hidden" 
            id="doc-upload" 
            accept=".pdf,.docx,.txt,.md"
          />
          <label 
            htmlFor="doc-upload"
            className={`flex items-center gap-stack-sm px-4 py-2 border border-outline-variant rounded-lg text-label-md font-label-md text-on-surface-variant transition-colors cursor-pointer ${isIngesting || isLoading ? 'opacity-50 pointer-events-none' : 'hover:bg-surface-container-high'}`}
          >
            <span className="material-symbols-outlined text-[20px]">upload_file</span>
            {isIngesting ? "Đang xử lý..." : "Import Docs"}
          </label>
          <p className="text-[10px] text-outline font-bold uppercase tracking-widest">Support: PDF, DOCX, TXT, MD</p>
        </div>
        
        {/* Ingest Error */}
        {ingestError && (
          <div className="p-3 bg-red-50 border border-red-200 rounded-xl text-red-700 text-body-md flex items-center gap-2">
            <span className="material-symbols-outlined text-red-500">error</span>
            {ingestError}
            <button className="ml-auto p-1 text-red-400 hover:text-red-600" onClick={() => setIngestError(null)}>
              <span className="material-symbols-outlined text-[18px]">close</span>
            </button>
          </div>
        )}

        {/* Ingest Progress */}
        {isIngesting && (
          <div className="flex items-center gap-stack-sm p-3 bg-primary/5 border border-primary/20 rounded-xl">
            <span className="w-4 h-4 border-2 border-primary border-t-transparent rounded-full animate-spin"></span>
            <p className="text-[12px] text-primary font-bold">Backend đang embedding...</p>
          </div>
        )}

        {/* Accumulated Imported Files List */}
        {importedFiles.length > 0 && (
          <div className="space-y-stack-sm">
            <p className="text-[10px] font-bold text-outline uppercase tracking-wider px-1">Imported Documents ({importedFiles.length})</p>
            <div className="flex flex-wrap gap-2">
              {importedFiles.map((file, idx) => (
                <div
                  key={`file-${idx}`}
                  className="flex items-center gap-1.5 px-3 py-1.5 bg-surface-container-low border border-outline-variant/30 rounded-full text-[11px] font-bold group hover:border-primary/40 transition-colors"
                  title={file.name}
                >
                  <span className={`w-1.5 h-1.5 rounded-full ${file.status === 'new' ? 'bg-green-500' : 'bg-blue-500'}`}></span>
                  <span className="truncate max-w-[180px] text-on-surface-variant">{file.name}</span>
                  <button
                    className="ml-0.5 text-outline hover:text-error transition-colors opacity-0 group-hover:opacity-100"
                    onClick={() => handleRemoveFile(file.name)}
                    title="Xoá file này khỏi context"
                  >
                    <span className="material-symbols-outlined text-[14px]">close</span>
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
      
      {/* Hidden controls */}
      <div className="flex flex-col md:flex-row gap-4 mt-stack-md mb-stack-md">
        <label className="flex items-center gap-2 text-label-md text-on-surface-variant">
          Kết quả tìm kiếm: 
          <input 
            type="number" 
            min="1" max="10" 
            className="w-16 bg-surface-container-lowest border border-outline-variant rounded p-1 text-on-surface outline-none"
            value={nResults}
            onChange={e => setNResults(e.target.value)}
            disabled={isLoading}
          />
        </label>
        <label className="flex items-center gap-2 text-label-md text-on-surface-variant cursor-pointer">
          <input 
            type="checkbox" 
            className="rounded border-outline-variant text-primary focus:ring-primary"
            checked={allowFallback}
            onChange={e => setAllowFallback(e.target.checked)}
            disabled={isLoading}
          />
          Cho phép fallback khi không có context
        </label>
      </div>

      <div className="flex justify-end mt-stack-md">
        <button 
          onClick={handleSubmit}
          disabled={isLoading || requirement.trim().length < 3 || isIngesting}
          className="bg-primary text-on-primary px-8 py-3 rounded-lg font-label-md text-label-md hover:opacity-90 active:scale-95 transition-all flex items-center gap-stack-sm shadow-md disabled:opacity-50"
        >
          {isLoading ? (
             <><span className="w-4 h-4 border-2 border-on-primary border-t-transparent rounded-full animate-spin"></span> ĐANG PHÂN TÍCH...</>
          ) : (
            <>🚀 PHÂN TÍCH & TẠO TASK</>
          )}
        </button>
      </div>
    </section>
  );
}
