import { bulkUploadProducts } from '../../services/api_v2.js';
import { showToast } from '../../utils/toast.js';

export function renderBulkImport() {
    return `
    <section class="panel">
      <h2>Bulk import</h2>
      <p class="muted">Upload an Excel sheet with columns <b>name, description, price, category, image</b> (optional: size, color) and a .zip of the images. Each <b>image</b> value must match a file name in the zip, like <code>red-shirt.jpg</code>. Images up to 5 MB each.</p>
      <label class="field"><span>Excel file (.xlsx)</span>
        <input type="file" accept=".xlsx" id="bulkExcelInput" class="input" /></label>
      <label class="field"><span>Images (.zip)</span>
        <input type="file" accept=".zip" id="bulkZipInput" class="input" /></label>
      <button id="bulkUploadBtn" class="btn btn-secondary">Upload and import</button>
      <div id="bulkReport" class="report" hidden></div>
    </section>`;
}

export function setupBulkImportEvents(rerender) {
    document.getElementById('bulkUploadBtn')?.addEventListener('click', async () => {
        const excelFile = document.getElementById('bulkExcelInput')?.files?.[0];
        const zipFile = document.getElementById('bulkZipInput')?.files?.[0];
        if (!excelFile || !zipFile) {
            showToast('Choose both the Excel file and the images zip.', 'info');
            return;
        }
        const btn = document.getElementById('bulkUploadBtn');
        btn.textContent = 'Importing…';
        btn.disabled = true;
        try {
            const result = await bulkUploadProducts(excelFile, zipFile);
            showToast(`${result.inserted} product(s) added${result.failed ? `, ${result.failed} skipped` : ''}.`,
                result.failed ? 'info' : 'success');
            if (result.failed) {
                // keep the report visible: re-render the page, then show the skipped rows
                await rerender();
                const report = document.getElementById('bulkReport');
                report.hidden = false;
                report.innerHTML = `<p><b>${result.failed} row(s) skipped:</b></p><ul>${result.errors.slice(0, 20)
                    .map(e => `<li>Row ${e.row}: ${e.reason.replace(/[<>&]/g, '')}</li>`).join('')}</ul>`;
            } else {
                rerender();
            }
        } catch (e) {
            showToast(`Import failed: ${e.message}`, 'error');
            btn.textContent = 'Upload and import';
            btn.disabled = false;
        }
    });
}
