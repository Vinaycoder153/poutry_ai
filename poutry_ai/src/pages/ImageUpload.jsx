import React, { useState, useRef } from 'react';
import { UploadCloud, ShieldAlert, FileImage, Sparkles, Info } from 'lucide-react';
import { api } from '../services/api';

// Self-contained high-quality SVG drawings for preset demonstration cases
const SVG_PRESET_HEALTHY = `data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 300" width="100%" height="100%">
  <rect width="400" height="300" fill="%23f3f4f6"/>
  <!-- Chicken Feathers Outer -->
  <path d="M50,150 C50,50 350,50 350,150 C350,250 50,250 50,150" fill="%23f9fafb" stroke="%23e5e7eb" stroke-width="4"/>
  <path d="M90,120 C110,90 140,80 180,90" stroke="%23d1d5db" fill="none" stroke-width="2"/>
  <path d="M220,90 C260,80 290,90 310,120" stroke="%23d1d5db" fill="none" stroke-width="2"/>
  <path d="M100,180 C120,210 150,220 180,210" stroke="%23d1d5db" fill="none" stroke-width="2"/>
  <path d="M220,210 C250,220 280,210 300,180" stroke="%23d1d5db" fill="none" stroke-width="2"/>
  
  <!-- Vent Cloaca Center (Healthy) -->
  <ellipse cx="200" cy="150" rx="30" ry="25" fill="%23fda4af" fill-opacity="0.6" stroke="%23f43f5e" stroke-width="1.5"/>
  <circle cx="200" cy="150" r="8" fill="%23e11d48"/>
  
  <!-- Text Label -->
  <text x="200" y="270" text-anchor="middle" font-family="sans-serif" font-weight="bold" font-size="14" fill="%234b5563">Preset 1: Normal healthy vent</text>
  <text x="200" y="35" text-anchor="middle" font-family="sans-serif" font-size="12" fill="%23059669" font-weight="bold">CLEAN / STANDARD CONDITION</text>
</svg>`;

const SVG_PRESET_WARNING = `data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 300" width="100%" height="100%">
  <rect width="400" height="300" fill="%23f3f4f6"/>
  <!-- Chicken Feathers Outer -->
  <path d="M50,150 C50,50 350,50 350,150 C350,250 50,250 50,150" fill="%23f9fafb" stroke="%23e5e7eb" stroke-width="4"/>
  <path d="M90,120 C110,90 140,80 180,90" stroke="%23c2410c" stroke-opacity="0.3" fill="none" stroke-width="2"/>
  
  <!-- Discoloration Pastey spots on feathers (Warning) -->
  <path d="M160,110 C170,115 180,105 185,115" stroke="%23d97706" fill="none" stroke-width="6" stroke-linecap="round"/>
  <path d="M220,110 C210,115 200,105 195,115" stroke="%23d97706" fill="none" stroke-width="5" stroke-linecap="round"/>
  <path d="M170,185 C180,180 185,190 195,180" stroke="%23b45309" fill="none" stroke-width="5" stroke-linecap="round"/>
  
  <!-- Vent Cloaca Center (Warning: Mild erythema) -->
  <ellipse cx="200" cy="150" rx="32" ry="26" fill="%23fecdd3" fill-opacity="0.8" stroke="%23e11d48" stroke-width="2"/>
  <circle cx="200" cy="150" r="10" fill="%23be123c"/>
  
  <!-- Text Label -->
  <text x="200" y="270" text-anchor="middle" font-family="sans-serif" font-weight="bold" font-size="14" fill="%234b5563">Preset 2: Mild Pasting &amp; Redness</text>
  <text x="200" y="35" text-anchor="middle" font-family="sans-serif" font-size="12" fill="%23d97706" font-weight="bold">WARNING: SUSPECTED VENT GLEET / SOILING</text>
</svg>`;

const SVG_PRESET_DANGER = `data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 300" width="100%" height="100%">
  <rect width="400" height="300" fill="%23f3f4f6"/>
  <!-- Chicken Feathers Outer -->
  <path d="M50,150 C50,50 350,50 350,150 C350,250 50,250 50,150" fill="%23f5f5f4" stroke="%23d6d3d1" stroke-width="4"/>
  
  <!-- Severe pasting and discharge spots (Danger) -->
  <path d="M150,140 C140,160 145,170 140,180" stroke="%23f5f5f4" stroke-opacity="0.9" fill="none" stroke-width="12" stroke-linecap="round"/>
  <path d="M250,140 C260,160 255,170 260,180" stroke="%23f5f5f4" stroke-opacity="0.9" fill="none" stroke-width="12" stroke-linecap="round"/>
  
  <!-- Yellowish fecal discharge streaks -->
  <path d="M170,170 C165,200 175,220 170,230" stroke="%23ca8a04" fill="none" stroke-width="8" stroke-linecap="round"/>
  <path d="M225,170 C230,200 220,220 225,230" stroke="%23ca8a04" fill="none" stroke-width="7" stroke-linecap="round"/>
  <path d="M195,185 C200,215 205,230 200,245" stroke="%23eab308" fill="none" stroke-width="9" stroke-linecap="round"/>
  
  <!-- Vent Cloaca Center (Danger: Severe swelling & ulceration) -->
  <ellipse cx="200" cy="150" rx="35" ry="28" fill="%23fda4af" fill-opacity="0.9" stroke="%23be123c" stroke-width="3"/>
  <ellipse cx="200" cy="150" rx="20" ry="15" fill="%23991b1b" stroke="%23dc2626" stroke-width="1.5"/>
  <circle cx="200" cy="150" r="7" fill="%237f1d1d"/>
  
  <!-- Text Label -->
  <text x="200" y="270" text-anchor="middle" font-family="sans-serif" font-weight="bold" font-size="14" fill="%234b5563">Preset 3: Severe Pastey Vent &amp; Swelling</text>
  <text x="200" y="35" text-anchor="middle" font-family="sans-serif" font-size="12" fill="%23dc2626" font-weight="bold">DANGER: SALMONELLA SCREENING TRIGGER</text>
</svg>`;

export default function ImageUpload({ onAnalysisComplete, settings }) {
  const [dragActive, setDragActive] = useState(false);
  const [selectedImage, setSelectedImage] = useState(null);
  const [selectedImageName, setSelectedImageName] = useState('');
  const [presetType, setPresetType] = useState(null); // 'healthy' | 'warning' | 'danger'
  const [analyzing, setAnalyzing] = useState(false);
  const [loaderStep, setLoaderStep] = useState(0);
  const [loaderProgress, setLoaderProgress] = useState(0);
  const [uploadError, setUploadError] = useState(null);
  
  const [imageFile, setImageFile] = useState(null);
  const fileInputRef = useRef(null);

  const loaderSteps = [
    'Initializing CloacaScan model v2.4-CLOACA-NET...',
    'Decompressing image channels and verifying contrast ratios...',
    'Segmenting poultry vent and cloacal ring regions...',
    'Extracting features (erythema index, pasted feathers, exudate density)...',
    'Classifying Salmonella risk index with confidence scoring...',
    'Finalizing diagnostic report and veterinany checklist...'
  ];

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const validateImageResolution = (file) => {
    return new Promise((resolve) => {
      const img = new Image();
      img.src = URL.createObjectURL(file);
      img.onload = () => {
        URL.revokeObjectURL(img.src);
        if (img.width < 200 || img.height < 200) {
          resolve({
            valid: false,
            message: `Image resolution is too low (${img.width}x${img.height}px). Please upload an image of at least 200x200 pixels.`
          });
        } else {
          resolve({ valid: true });
        }
      };
      img.onerror = () => {
        resolve({
          valid: false,
          message: "Failed to read image dimensions. Please upload a valid image file."
        });
      };
    });
  };

  const processImageFile = async (file) => {
    setUploadError(null);
    if (!file) return;

    // 1. File size validation (10MB)
    const maxSizeBytes = 10 * 1024 * 1024;
    if (file.size > maxSizeBytes) {
      setUploadError({
        title: "File Too Large",
        message: `The selected image is ${(file.size / (1024 * 1024)).toFixed(1)}MB, which exceeds the 10MB limit. Please upload a smaller image.`
      });
      setSelectedImage(null);
      setSelectedImageName('');
      setImageFile(null);
      return;
    }

    // 2. Format validation (.jpg, .jpeg, .png, .webp)
    const validExtensions = ['.jpg', '.jpeg', '.png', '.webp'];
    const fileExt = file.name.substring(file.name.lastIndexOf('.')).toLowerCase();
    if (!file.type.startsWith('image/') || !validExtensions.includes(fileExt)) {
      setUploadError({
        title: "Invalid File Type",
        message: "Only JPG, JPEG, PNG, and WEBP image formats are supported. Please upload a chicken vent image in these formats."
      });
      setSelectedImage(null);
      setSelectedImageName('');
      setImageFile(null);
      return;
    }

    // 3. Resolution check (client-side)
    const resValidation = await validateImageResolution(file);
    if (!resValidation.valid) {
      setUploadError({
        title: "Low Resolution Image",
        message: resValidation.message
      });
      setSelectedImage(null);
      setSelectedImageName('');
      setImageFile(null);
      return;
    }

    setImageFile(file);
    const reader = new FileReader();
    reader.onload = (e) => {
      setSelectedImage(e.target.result);
      setSelectedImageName(file.name);
      setPresetType(null); // Custom upload
    };
    reader.readAsDataURL(file);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      processImageFile(e.dataTransfer.files[0]);
    }
  };

  const handleChange = (e) => {
    e.preventDefault();
    if (e.target.files && e.target.files[0]) {
      processImageFile(e.target.files[0]);
    }
  };

  const selectPreset = (type, imgUrl, name) => {
    setSelectedImage(imgUrl);
    setSelectedImageName(name);
    setPresetType(type);
    setImageFile(null);
    setUploadError(null);
  };

  const startAnalysis = async () => {
    if (!selectedImage) return;

    setAnalyzing(true);
    setLoaderStep(0);
    setLoaderProgress(0);
    setUploadError(null);

    // Simulated progress bar updates while waiting for API
    let step = 0;
    const interval = setInterval(() => {
      step += 1;
      setLoaderStep(Math.min(step, loaderSteps.length - 1));
      setLoaderProgress(Math.min(90, (step / loaderSteps.length) * 100));
    }, 450);

    try {
      let uploadFile = imageFile;
      if (presetType) {
        const presetName = presetType === 'healthy' ? 'healthy' : presetType === 'warning' ? 'warning' : 'danger';
        const response = await fetch(`/presets/${presetName}.png`);
        const blob = await response.blob();
        uploadFile = new File([blob], selectedImageName, { type: 'image/png' });
      }

      if (!uploadFile) {
        throw new Error("No image file loaded. Please upload a photo or select a preset.");
      }

      const result = await api.predictImage(uploadFile);

      setLoaderProgress(100);
      clearInterval(interval);

      setTimeout(() => {
        setAnalyzing(false);
        onAnalysisComplete(result);
      }, 500);

    } catch (error) {
      clearInterval(interval);
      setAnalyzing(false);
      setUploadError({
        title: "AI Screening Rejected",
        message: error.message || "An unexpected error occurred during the analysis run."
      });
    }
  };

  const triggerResultGeneration = () => {
    // Generate simulated result based on the image type
    let status = 'healthy';
    let confidence = 96.8;
    let title = 'Normal Healthy Cloaca';
    let findings = [
      'Anatomical borders of the cloacal sphincter are clean and well-defined.',
      'No evidence of feather pasting, soil buildup, or fecal accumulation.',
      'Normal mucous membrane color without swelling or inflammatory erythema.',
      'No abnormal cloacal discharge or fluid leaks detected.'
    ];
    let actions = [
      'Maintain standard farm hygiene and litter status.',
      'Check feed line sanitize metrics.',
      'Log as standard healthy baseline.'
    ];

    if (presetType === 'warning') {
      status = 'warning';
      confidence = settings ? settings.warningThreshold + 8 : 78.4;
      title = 'Mild Pasting & Erythema Detected';
      findings = [
        'Moderate feather pasting identified along the lower cloacal margins.',
        'Mild redness (erythema) noted around the sphincter border.',
        'Litter status review recommended for the containing pen.',
        'Slight accumulation of light uric acid crystals on adjacent plumage.'
      ];
      actions = [
        'Isolate subject for detailed physical examination.',
        'Wipe the vent clean with a sanitized warm compress.',
        'Assess flock droppings for evidence of diarrhea or dysentery.',
        'Review vent ventilation and humidity levels in House Section 4B.'
      ];
    } else if (presetType === 'danger' || (!presetType && Math.random() > 0.5)) {
      // Custom uploads have a 50% chance of being high-risk for simulation variety
      status = 'danger';
      confidence = settings ? settings.dangerThreshold + 6 : 91.2;
      title = 'Abnormal Vent Discharge (High Salmonella Risk)';
      findings = [
        'Severe pasting of feathers with dense, white fecal discharge.',
        'Pronounced swelling and enlargement of the cloacal opening.',
        'Ulceration or skin erosion visible on the ventral skin border.',
        'High thermal radiation signatures indicated in localized cloacal zone.'
      ];
      actions = [
        'IMMEDIATE ISOLATION: Remove the chicken from the main flock immediately.',
        'QUARANTINE PROTOCOL: Restrict entry to containing house and change boot wash sanitizer.',
        'ALERT VET: Flag this report to Dr. Robert Carter or the attending flock vet.',
        'DIAGNOSTIC TEST: Collect fecal swabs for PCR or Salmonella bacterial culture.',
        'Disinfect surrounding roosting areas and drinker nipples.'
      ];
    }

    const result = {
      id: `CS-${Math.floor(100000 + Math.random() * 900000)}`,
      date: new Date().toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' }),
      time: new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' }),
      image: selectedImage,
      imageName: selectedImageName,
      status,
      confidence,
      title,
      findings,
      actions,
      reviewed: false,
      flagged: status === 'danger',
      modelVersion: 'V2.4-CLOACA-NET',
      analysisTime: '1.42s'
    };

    setAnalyzing(false);
    onAnalysisComplete(result);
  };

  return (
    <div className="page-container">
      <div className="page-header">
        <div>
          <h2 style={{ fontSize: '24px', fontWeight: 700 }}>Upload Cloacal Image</h2>
          <p className="page-desc">Analyze vent conditions to identify pasting, inflammation, and Salmonella indicators</p>
        </div>
      </div>

      <div className="upload-layout">
        {/* Left Side: Upload zone and test presets */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          
          {/* File Dropzone */}
          <div 
            className={`dropzone-container ${dragActive ? 'drag-active' : ''}`}
            onDragEnter={handleDrag}
            onDragOver={handleDrag}
            onDragLeave={handleDrag}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current.click()}
          >
            <input 
              type="file" 
              ref={fileInputRef}
              className="file-input"
              accept="image/jpeg, image/png, image/jpg, image/webp"
              onChange={handleChange}
            />
            <UploadCloud size={48} className="dropzone-icon" />
            <h3 className="dropzone-title">Drag &amp; drop chicken photo</h3>
            <p className="dropzone-subtitle">Supports JPG, PNG, and WEBP formats (Max size 10MB)</p>
            <button type="button" className="btn btn-secondary">
              Browse Files
            </button>
          </div>

          {/* Presets Panel */}
          <div className="panel">
            <h4 className="preset-title">
              <Sparkles size={14} className="text-primary" style={{ display: 'inline-block', marginRight: '6px', verticalAlign: 'middle' }} />
              Quick Sandbox Presets (Click to Load)
            </h4>
            <p style={{ fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '14px' }}>
              Select a calibrated demo case to test the AI detection thresholds and analysis reports without uploading a photo.
            </p>
            
            <div className="presets-grid">
              <div 
                className={`preset-card ${presetType === 'healthy' ? 'active' : ''}`} 
                onClick={() => selectPreset('healthy', '/presets/healthy.png', 'healthy_01.png')}
                style={{ border: presetType === 'healthy' ? '2px solid var(--primary-color)' : '' }}
              >
                <img src="/presets/healthy.png" className="preset-img-thumb" alt="Healthy preset" />
                <span className="preset-label text-healthy" style={{ color: 'var(--healthy-color)' }}>Healthy Case</span>
              </div>

              <div 
                className={`preset-card ${presetType === 'warning' ? 'active' : ''}`} 
                onClick={() => selectPreset('warning', '/presets/warning.png', 'dirty_01.png')}
                style={{ border: presetType === 'warning' ? '2px solid var(--warning-color)' : '' }}
              >
                <img src="/presets/warning.png" className="preset-img-thumb" alt="Warning preset" />
                <span className="preset-label text-warning" style={{ color: 'var(--warning-color)' }}>Warning Case</span>
              </div>

              <div 
                className={`preset-card ${presetType === 'danger' ? 'active' : ''}`} 
                onClick={() => selectPreset('danger', '/presets/danger.png', 'prolapse_01.png')}
                style={{ border: presetType === 'danger' ? '2px solid var(--danger-color)' : '' }}
              >
                <img src="/presets/danger.png" className="preset-img-thumb" alt="Danger preset" />
                <span className="preset-label text-danger" style={{ color: 'var(--danger-color)' }}>High-Risk Case</span>
              </div>
            </div>
          </div>

        </div>

        {/* Right Side: Image Preview & Trigger button */}
        <div className="preview-container">
          <h3 style={{ fontSize: '16px', fontWeight: 600, marginBottom: '12px' }}>Selected Image Preview</h3>
          
          <div className="preview-image-wrapper">
            {selectedImage ? (
              <img src={selectedImage} alt="Chicken vent preview" className="preview-image" />
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '8px', color: 'var(--text-tertiary)' }}>
                <FileImage size={40} />
                <span style={{ fontSize: '13px' }}>No image loaded</span>
              </div>
            )}

            {/* Simulated AI Progress Overlay */}
            {analyzing && (
              <div className="loader-overlay">
                <div className="loader-spinner"></div>
                <div className="loader-step-text">
                  {loaderSteps[loaderStep]}
                </div>
                <div className="loader-bar-bg">
                  <div className="loader-bar-fill" style={{ width: `${loaderProgress}%` }}></div>
                </div>
                <span style={{ fontSize: '11px', color: 'var(--text-secondary)', marginTop: '8px' }}>
                  Processing... {Math.round(loaderProgress)}%
                </span>
              </div>
            )}
          </div>

          {selectedImage && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '13px' }}>
                <span style={{ color: 'var(--text-secondary)', fontWeight: 500 }}>Filename:</span>
                <span style={{ fontWeight: 600, maxWidth: '240px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {selectedImageName}
                </span>
              </div>
              <button 
                onClick={startAnalysis} 
                disabled={analyzing}
                className="btn btn-primary btn-block"
                style={{ padding: '12px', fontSize: '15px' }}
              >
                <Sparkles size={16} />
                Execute AI Diagnostic Run
              </button>
            </div>
          )}

          {!selectedImage && !uploadError && (
            <div style={{
              display: 'flex',
              gap: '10px',
              backgroundColor: 'var(--bg-secondary)',
              border: '1px solid var(--border-color)',
              borderRadius: 'var(--radius-md)',
              padding: '16px',
              fontSize: '13px',
              color: 'var(--text-secondary)',
              marginTop: 'auto'
            }}>
              <Info size={20} className="text-primary" style={{ flexShrink: 0, marginTop: '2px', color: 'var(--primary-color)' }} />
              <div>
                <strong style={{ display: 'block', color: 'var(--text-primary)', marginBottom: '4px' }}>
                  Screening Instructions
                </strong>
                Position the camera 10-15 cm directly facing the chicken's vent. Ensure adequate lighting, clean off extreme mud blocks, and verify the vent/cloacal ring is fully centered in the frame.
              </div>
            </div>
          )}

          {uploadError && (
            <div style={{
              display: 'flex',
              flexDirection: 'column',
              gap: '12px',
              backgroundColor: 'var(--danger-light)',
              border: '1px solid var(--danger-border)',
              borderRadius: 'var(--radius-md)',
              padding: '16px',
              fontSize: '13px',
              color: 'var(--text-primary)',
              marginTop: selectedImage ? '16px' : 'auto',
              boxShadow: 'var(--shadow-sm)'
            }}>
              <div style={{ display: 'flex', gap: '10px', alignItems: 'flex-start' }}>
                <ShieldAlert size={20} className="text-danger" style={{ color: 'var(--danger-color)', flexShrink: 0, marginTop: '2px' }} />
                <div>
                  <strong style={{ fontSize: '14px', color: 'var(--danger-color)', display: 'block' }}>
                    {uploadError.title}
                  </strong>
                  <span style={{ display: 'block', color: 'var(--text-secondary)', marginTop: '4px', lineHeight: '1.4' }}>
                    {uploadError.message}
                  </span>
                </div>
              </div>
              
              <div style={{
                marginTop: '4px',
                paddingTop: '10px',
                borderTop: '1px solid var(--danger-border)',
                display: 'flex',
                flexDirection: 'column',
                gap: '6px'
              }}>
                <span style={{ fontWeight: 600, fontSize: '11px', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                  Tips for a successful scan:
                </span>
                <ul style={{ paddingLeft: '16px', margin: 0, color: 'var(--text-secondary)', display: 'flex', flexDirection: 'column', gap: '4px', listStyleType: 'disc' }}>
                  <li><strong>Check Distance:</strong> Hold camera 10-15 cm directly from the vent.</li>
                  <li><strong>Adjust Lighting:</strong> Ensure direct, bright lighting without harsh shadows.</li>
                  <li><strong>Verify Centering:</strong> Center the cloacal ring directly in the frame.</li>
                  <li><strong>Clean Obstructions:</strong> Clean off major dry mud clumps from surrounding feathers.</li>
                </ul>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
