import { useState, useRef, useEffect } from 'react';
import { uploadDocumentsAsync, getIngestStatus } from '../lib/api';

export default function RequirementInputPanel({ onSubmit, isLoading }) {
  const [requirement, setRequirement] = useState('');
  const [nResults, setNResults] = useState(5);
  const [allowFallback, setAllowFallback] = useState(false);

  // Ingest states
  const [isIngesting, setIsIngesting] = useState(false);
  const [ingestData, setIngestData] = useState(null);  // IngestStatusResponse
  const [ingestError, setIngestError] = useState(null);
  const [jobId, setJobId] = useState(null);

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

  const handleSubmit = (e) => {
    e.preventDefault();
    if (requirement.trim().length < 3) return;
    
    onSubmit({
      requirement,
      n_results: parseInt(nResults, 10),
      allow_fallback_without_context: allowFallback,
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
      const jobResponse = await uploadDocumentsAsync(files);
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

        {/* Ingest Progress / Result */}
        {(isIngesting || ingestData) && (
          <div className="space-y-stack-sm">
            <p className="text-[10px] font-bold text-outline uppercase tracking-wider px-1">Imported Documents</p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-stack-sm">
              <div className="flex items-center justify-between p-3 bg-surface-container-low border border-outline-variant/30 rounded-xl">
                <div className="flex items-center gap-stack-sm">
                  <div className="p-2 bg-primary/10 rounded-lg text-primary">
                    <span className="material-symbols-outlined text-[20px]">
                      {isIngesting ? 'pending' : 'library_books'}
                    </span>
                  </div>
                  <div className="flex-1 w-full max-w-full min-w-0">
                    <p className="text-label-md font-bold truncate">
                      {isIngesting ? 'Đang xử lý...' : 'Import Hoàn Tất'}
                    </p>
                    {isIngesting ? (
                      <p className="text-[10px] text-primary font-bold flex items-center gap-1">
                        <span className="w-4 h-4 border-2 border-primary border-t-transparent rounded-full animate-spin"></span>
                        Backend đang embedding... 
                      </p>
                    ) : (
                      <div className="flex flex-col gap-1 mt-1">
                        {ingestData?.result?.indexed_files?.map((filename, idx) => (
                          <p key={`idx-${idx}`} className="text-[10px] text-green-600 font-bold flex items-center gap-1 truncate" title={filename}>
                            <span className="w-1.5 h-1.5 bg-green-500 rounded-full animate-pulse"></span>
                            {filename} (Đã thêm)
                          </p>
                        ))}
                        {ingestData?.result?.skipped_files?.map((filename, idx) => (
                          <p key={`skip-${idx}`} className="text-[10px] text-blue-600 font-bold flex items-center gap-1 truncate" title={filename}>
                            <span className="material-symbols-outlined text-blue-500 text-[14px]" style={{fontVariationSettings: "'FILL' 1"}}>verified</span>
                            {filename} (Đã có sẵn)
                          </p>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
                {!isIngesting && ingestData && (
                  <button className="p-1 text-outline hover:text-error transition-colors" onClick={() => setIngestData(null)}>
                    <span className="material-symbols-outlined">close</span>
                  </button>
                )}
              </div>
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
