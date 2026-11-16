// CS2 Arsenal Web UI - Frontend Application
document.addEventListener('DOMContentLoaded', () => {
    // State
    const state = {
        catalog: null,
        inventory: null,
        activeTab: 'knives',
        activeTeam: 0, // 0 = Ambos, 3 = CT, 2 = TR
        teamLockedByWeapon: false,
        searchQuery: '',
        selectedItem: null,
        selectedSkin: null,
        selectedGemPreset: null,
        selectedWeaponFilter: 'ALL',
        currentSteamId: '76561198816182970'
    };

    // DOM Elements
    const itemsGrid = document.getElementById('itemsGrid');
    const searchInput = document.getElementById('searchInput');
    const steamidInput = document.getElementById('steamidInput');
    const gemChipsContainer = document.getElementById('gemChipsContainer');
    const gemPresetsBar = document.getElementById('gemPresetsBar');
    const weaponPillsBar = document.getElementById('weaponPillsBar');
    const toastContainer = document.getElementById('toastContainer');
    const tabButtons = document.querySelectorAll('.tab-btn');
    const teamButtons = document.querySelectorAll('.team-btn');
    const teamLockBadge = document.getElementById('teamLockBadge');

    // Inspect Elements
    const inspectImage = document.getElementById('inspectImage');
    const inspectName = document.getElementById('inspectName');
    const inspectType = document.getElementById('inspectType');
    const inspectRarity = document.getElementById('inspectRarity');
    const floatSlider = document.getElementById('floatSlider');
    const floatValueDisplay = document.getElementById('floatValueDisplay');
    const seedInput = document.getElementById('seedInput');
    const paintIdInput = document.getElementById('paintIdInput');
    const nametagInput = document.getElementById('nametagInput');
    const stattrakCheckbox = document.getElementById('stattrakCheckbox');
    const stattrakCountInput = document.getElementById('stattrakCountInput');
    const btnEquipAction = document.getElementById('btnEquipAction');
    const btnInspectAction = document.getElementById('btnInspectAction');
    const knifeSkinSelectGroup = document.getElementById('knifeSkinSelectGroup');
    const knifeSkinSelect = document.getElementById('knifeSkinSelect');

    // Elementos do Modal de Inspeção
    const inspectModalBackdrop = document.getElementById('inspectModalBackdrop');
    const modalCloseBtn = document.getElementById('modalCloseBtn');
    const modalRarityBadge = document.getElementById('modalRarityBadge');
    const modalWeaponName = document.getElementById('modalWeaponName');
    const modalWeaponType = document.getElementById('modalWeaponType');
    const modalInspectImage = document.getElementById('modalInspectImage');
    const inspectStage = document.getElementById('inspectStage');
    const stageTurntable = document.getElementById('stageTurntable');
    const stageReflection = document.getElementById('stageReflection');
    const btnToggleRotate = document.getElementById('btnToggleRotate');
    const btnFlipSide = document.getElementById('btnFlipSide');
    const btnResetView = document.getElementById('btnResetView');
    const modalFloatVal = document.getElementById('modalFloatVal');
    const modalSeedVal = document.getElementById('modalSeedVal');
    const modalPaintVal = document.getElementById('modalPaintVal');
    const modalStattrakBox = document.getElementById('modalStattrakBox');
    const modalStattrakVal = document.getElementById('modalStattrakVal');
    const modalNametagBox = document.getElementById('modalNametagBox');
    const modalNametagVal = document.getElementById('modalNametagVal');
    const btnLaunchCs2Inspect = document.getElementById('btnLaunchCs2Inspect');
    const btnCopyInspectLink = document.getElementById('btnCopyInspectLink');
    const btnCopyConsoleCmd = document.getElementById('btnCopyConsoleCmd');
    const btnOpenWeb3D = document.getElementById('btnOpenWeb3D');

    // Estado da Inspeção 3D
    let currentInspectData = null;
    let inspectRotationY = 0;
    let inspectRotationX = 0;
    let inspectScaleX = 1;
    let isAutoRotating = false;
    let autoRotateAnimId = null;
    let isDraggingStage = false;
    let dragStartX = 0;
    let dragStartY = 0;

    // =========================================================================
    // Regras Oficiais de Equipes / Lados do CS2
    // =========================================================================
    const WEAPON_TEAM_RULES = {
        // Terroristas Apenas (TR = 2)
        'weapon_ak47': { team: 2, label: 'Terroristas (TR)', name: 'AK-47' },
        'weapon_galilar': { team: 2, label: 'Terroristas (TR)', name: 'Galil AR' },
        'weapon_sg556': { team: 2, label: 'Terroristas (TR)', name: 'SG 553' },
        'weapon_g3sg1': { team: 2, label: 'Terroristas (TR)', name: 'G3SG1' },
        'weapon_glock': { team: 2, label: 'Terroristas (TR)', name: 'Glock-18' },
        'weapon_tec9': { team: 2, label: 'Terroristas (TR)', name: 'Tec-9' },
        'weapon_mac10': { team: 2, label: 'Terroristas (TR)', name: 'MAC-10' },
        'weapon_sawedoff': { team: 2, label: 'Terroristas (TR)', name: 'Sawed-Off' },

        // Contraterroristas Apenas (CT = 3)
        'weapon_m4a1': { team: 3, label: 'Contraterroristas (CT)', name: 'M4A4' },
        'weapon_m4a1_silencer': { team: 3, label: 'Contraterroristas (CT)', name: 'M4A1-S' },
        'weapon_famas': { team: 3, label: 'Contraterroristas (CT)', name: 'FAMAS' },
        'weapon_aug': { team: 3, label: 'Contraterroristas (CT)', name: 'AUG' },
        'weapon_scar20': { team: 3, label: 'Contraterroristas (CT)', name: 'SCAR-20' },
        'weapon_usp_silencer': { team: 3, label: 'Contraterroristas (CT)', name: 'USP-S' },
        'weapon_hkp2000': { team: 3, label: 'Contraterroristas (CT)', name: 'P2000' },
        'weapon_fiveseven': { team: 3, label: 'Contraterroristas (CT)', name: 'Five-SeveN' },
        'weapon_mp9': { team: 3, label: 'Contraterroristas (CT)', name: 'MP9' },
        'weapon_mag7': { team: 3, label: 'Contraterroristas (CT)', name: 'MAG-7' }
    };

    const DEFINDEX_TEAM_RULES = {
        // TR
        7: WEAPON_TEAM_RULES['weapon_ak47'],
        13: WEAPON_TEAM_RULES['weapon_galilar'],
        39: WEAPON_TEAM_RULES['weapon_sg556'],
        11: WEAPON_TEAM_RULES['weapon_g3sg1'],
        4: WEAPON_TEAM_RULES['weapon_glock'],
        30: WEAPON_TEAM_RULES['weapon_tec9'],
        17: WEAPON_TEAM_RULES['weapon_mac10'],
        35: WEAPON_TEAM_RULES['weapon_sawedoff'],

        // CT
        16: WEAPON_TEAM_RULES['weapon_m4a1'],
        60: WEAPON_TEAM_RULES['weapon_m4a1_silencer'],
        10: WEAPON_TEAM_RULES['weapon_famas'],
        8: WEAPON_TEAM_RULES['weapon_aug'],
        38: WEAPON_TEAM_RULES['weapon_scar20'],
        61: WEAPON_TEAM_RULES['weapon_usp_silencer'],
        32: WEAPON_TEAM_RULES['weapon_hkp2000'],
        3: WEAPON_TEAM_RULES['weapon_fiveseven'],
        34: WEAPON_TEAM_RULES['weapon_mp9'],
        27: WEAPON_TEAM_RULES['weapon_mag7']
    };

    function syncTeamRestrictions(target) {
        // Se estiver na aba do inventário (Arsenal Equipado), os botões funcionam apenas como filtro de exibição e nunca devem ser travados!
        if (state.activeTab === 'inventory') {
            if (teamLockBadge) teamLockBadge.style.display = 'none';
            teamButtons.forEach(btn => {
                btn.classList.remove('disabled');
                btn.disabled = false;
                btn.removeAttribute('title');
                const btnTeam = parseInt(btn.getAttribute('data-team'), 10);
                btn.classList.toggle('active', btnTeam === state.activeTeam);
            });
            return;
        }

        let rule = null;
        if (typeof target === 'string' && target !== 'ALL') {
            rule = WEAPON_TEAM_RULES[target] || null;
        } else if (typeof target === 'number') {
            rule = DEFINDEX_TEAM_RULES[target] || null;
        }

        if (rule) {
            state.activeTeam = rule.team;
            state.teamLockedByWeapon = true;

            if (teamLockBadge) {
                teamLockBadge.style.display = 'inline-block';
                teamLockBadge.className = `team-lock-badge ${rule.team === 2 ? 'tr' : 'ct'}`;
                teamLockBadge.textContent = rule.team === 2 ? '🔒 EXCLUSIVO TR' : '🔒 EXCLUSIVO CT';
            }

            teamButtons.forEach(btn => {
                const btnTeam = parseInt(btn.getAttribute('data-team'), 10);
                if (btnTeam === rule.team) {
                    btn.classList.add('active');
                    btn.classList.remove('disabled');
                    btn.disabled = false;
                    btn.title = `Equipar para ${rule.label} (Exclusivo desta arma)`;
                } else {
                    btn.classList.remove('active');
                    btn.classList.add('disabled');
                    btn.disabled = true;
                    btn.title = `${rule.name} é exclusiva dos ${rule.label}! Não disponível para ${btnTeam === 0 ? 'Ambos' : btnTeam === 3 ? 'CT' : 'TR'}.`;
                }
            });
        } else {
            // Arma universal (AWP, Deagle, etc.) ou "Todas as Armas" ou Facas/Luvas
            if (teamLockBadge) teamLockBadge.style.display = 'none';

            if (state.teamLockedByWeapon) {
                state.activeTeam = 0; // Retorna para AMBOS
                state.teamLockedByWeapon = false;
            }

            teamButtons.forEach(btn => {
                btn.classList.remove('disabled');
                btn.disabled = false;
                btn.removeAttribute('title');
                const btnTeam = parseInt(btn.getAttribute('data-team'), 10);
                btn.classList.toggle('active', btnTeam === state.activeTeam);
            });
        }
    }

    // Inicialização
    init();

    async function init() {
        setupEventListeners();
        await fetchCatalog();
        await fetchInventory();
        renderGemPresets();
        updateCategoryView();
    }

    function setupEventListeners() {
        // Tab switching
        tabButtons.forEach(btn => {
            btn.addEventListener('click', () => {
                tabButtons.forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                state.activeTab = btn.getAttribute('data-tab');
                state.selectedWeaponFilter = 'ALL';
                updateCategoryView();
            });
        });

        // Team switching
        teamButtons.forEach(btn => {
            btn.addEventListener('click', () => {
                if (btn.disabled || btn.classList.contains('disabled')) return;
                teamButtons.forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                state.activeTeam = parseInt(btn.getAttribute('data-team'), 10);
                state.teamLockedByWeapon = false;
                renderGrid();
            });
        });

        // Search with debounce
        let searchTimeout = null;
        searchInput.addEventListener('input', (e) => {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                state.searchQuery = e.target.value.toLowerCase().trim();
                renderGrid();
            }, 150);
        });

        // SteamID change
        steamidInput.addEventListener('change', async (e) => {
            state.currentSteamId = e.target.value.trim();
            await fetchInventory();
            renderGrid();
        });

        // Float Slider
        floatSlider.addEventListener('input', (e) => {
            updateFloatDisplay(parseFloat(e.target.value));
        });

        // Knife individual skin dropdown change
        if (knifeSkinSelect) {
            knifeSkinSelect.addEventListener('change', (e) => {
                handleIndividualKnifeSkinChange(e.target.value);
            });
        }

        // Equip Button
        btnEquipAction.addEventListener('click', () => {
            equipSelectedItem();
        });

        // Inspect Button
        if (btnInspectAction) {
            btnInspectAction.addEventListener('click', () => {
                openInspectModal();
            });
        }

        // Modal Close Button & Backdrop Click
        if (modalCloseBtn) {
            modalCloseBtn.addEventListener('click', closeInspectModal);
        }
        if (inspectModalBackdrop) {
            inspectModalBackdrop.addEventListener('click', (e) => {
                if (e.target === inspectModalBackdrop) closeInspectModal();
            });
        }
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && inspectModalBackdrop && inspectModalBackdrop.style.display !== 'none') {
                closeInspectModal();
            }
        });

        // Configurar Interações 3D do Palco
        setupStageInteractions();
    }

    function updateCategoryView() {
        // Controlar barras superiores
        if (state.activeTab === 'knives') {
            gemPresetsBar.style.display = 'flex';
            weaponPillsBar.style.display = 'none';
        } else if (state.activeTab === 'rifles' || state.activeTab === 'pistols') {
            gemPresetsBar.style.display = 'none';
            weaponPillsBar.style.display = 'flex';
            renderWeaponPills();
        } else {
            gemPresetsBar.style.display = 'none';
            weaponPillsBar.style.display = 'none';
        }

        // Ajustar rótulo do filtro de equipe
        const filterLabel = document.querySelector('.filter-label');
        if (filterLabel) {
            if (state.activeTab === 'inventory') {
                filterLabel.textContent = 'FILTRAR EQUIPE:';
            } else {
                filterLabel.textContent = 'EQUIPAR PARA:';
            }
        }

        // Sincronizar restrições de equipe (TR / CT / AMBOS)
        if (state.activeTab === 'rifles' || state.activeTab === 'pistols') {
            syncTeamRestrictions(state.selectedWeaponFilter);
        } else {
            syncTeamRestrictions(null);
        }

        renderGrid();
    }

    function updateFloatDisplay(val) {
        let condition = 'Factory New';
        if (val >= 0.45) condition = 'Battle-Scarred';
        else if (val >= 0.38) condition = 'Well-Worn';
        else if (val >= 0.15) condition = 'Field-Tested';
        else if (val >= 0.07) condition = 'Minimal Wear';

        floatValueDisplay.textContent = `${val.toFixed(4)} (${condition})`;
    }

    async function fetchCatalog() {
        try {
            const res = await fetch('/api/catalog');
            state.catalog = await res.json();
        } catch (err) {
            console.error('Falha ao carregar catálogo:', err);
            showToast('Erro ao carregar catálogo do servidor', '❌');
        }
    }

    async function fetchInventory() {
        try {
            const res = await fetch(`/api/inventory?steamid=${state.currentSteamId}`);
            state.inventory = await res.json();
        } catch (err) {
            console.error('Falha ao carregar inventário:', err);
        }
    }

    // =========================================================================
    // Gem Presets Globais para Facas
    // =========================================================================
    function renderGemPresets() {
        if (!state.catalog || !state.catalog.gem_presets) return;
        gemChipsContainer.innerHTML = '';

        state.catalog.gem_presets.forEach(preset => {
            const chip = document.createElement('div');
            const isActive = state.selectedGemPreset && state.selectedGemPreset.paint_id === preset.paint_id;
            chip.className = `gem-chip ${preset.css_class} ${isActive ? 'active' : ''}`;
            chip.innerHTML = `<span>✨</span> ${preset.name}`;
            chip.title = `${preset.name} (Paint ID: ${preset.paint_id})`;

            chip.addEventListener('click', () => {
                applyGlobalGemPreset(preset);
            });

            gemChipsContainer.appendChild(chip);
        });
    }

    function applyGlobalGemPreset(preset) {
        state.selectedGemPreset = preset;

        // Atualizar destaque visual dos chips
        document.querySelectorAll('.gem-chip').forEach(c => c.classList.remove('active'));
        renderGemPresets();

        // Atualizar inputs de customização
        paintIdInput.value = preset.paint_id;
        seedInput.value = preset.seed;
        floatSlider.value = preset.wear;
        updateFloatDisplay(preset.wear);

        // Se houver uma faca inspecionada, atualizar a inspeção lateral imediatamente
        if (state.selectedItem && state.selectedItem.type === 'knife') {
            const knife = state.selectedItem.knife;
            const skinInfo = getKnifeSkinForPreset(knife, preset);

            state.selectedItem.image_url = skinInfo.image_url;
            state.selectedItem.currentSkin = skinInfo;

            inspectImage.src = skinInfo.image_url;
            inspectName.textContent = `${knife.name} | ${skinInfo.name}`;
            inspectType.textContent = preset.paint_id > 0 ? `Gema Especial (Paint ID: ${preset.paint_id})` : 'Faca Vanilla / Padrão';
            
            if (preset.paint_id > 0) {
                inspectRarity.textContent = `★ ${preset.badge || 'ESPECIAL'}`;
                inspectRarity.style.background = getPresetBadgeColor(preset.css_class);
                inspectRarity.style.color = '#fff';
            } else {
                inspectRarity.textContent = '★ EXTRAORDINÁRIO';
                inspectRarity.style.background = 'var(--accent-gold)';
                inspectRarity.style.color = '#000';
            }
        }

        // Re-renderizar o grid de facas: TODAS as facas mudam o visual instantaneamente!
        renderGrid();

        if (preset.paint_id === 0) {
            showToast('Visual padrão (Vanilla) aplicado a todas as facas!', '🗡️');
        } else {
            showToast(`Acabamento ${preset.name} aplicado a todas as facas!`, '💎');
        }
    }

    // Tabela de variantes alternativas de Paint IDs por modelo de faca na Valve (CS2)
    const PRESET_ALIASES = {
        // Doppler Phase 2 (Pink)
        419: {
            'weapon_knife_butterfly': 618,
            'weapon_knife_push': 618,
            'weapon_knife_widowmaker': 853
        },
        // Doppler Sapphire
        416: {
            'weapon_knife_butterfly': 619,
            'weapon_knife_push': 619
        },
        // Doppler Black Pearl
        417: {
            'weapon_knife_butterfly': 617,
            'weapon_knife_push': 617
        },
        // Doppler Phase 1
        418: {
            'weapon_knife_widowmaker': 852
        },
        // Doppler Phase 3
        420: {
            'weapon_knife_widowmaker': 854
        },
        // Doppler Phase 4 (Blue)
        421: {
            'weapon_knife_widowmaker': 855
        },
        // Lore (Clean)
        562: {
            'weapon_bayonet': 558,
            'weapon_knife_flip': 559,
            'weapon_knife_gut': 560,
            'weapon_knife_karambit': 561,
            'weapon_knife_m9_bayonet': 562,
            'weapon_knife_survival_bowie': 1104,
            'weapon_knife_butterfly': 1105,
            'weapon_knife_falchion': 1106,
            'weapon_knife_tactical': 1107,
            'weapon_knife_push': 1108
        },
        // Autotronic
        573: {
            'weapon_bayonet': 573,
            'weapon_knife_flip': 574,
            'weapon_knife_gut': 575,
            'weapon_knife_karambit': 576,
            'weapon_knife_m9_bayonet': 577,
            'weapon_knife_survival_bowie': 1114,
            'weapon_knife_butterfly': 1115,
            'weapon_knife_falchion': 1116,
            'weapon_knife_tactical': 1117,
            'weapon_knife_push': 1118
        }
    };

    function getKnifeSkinForPreset(knife, preset) {
        if (!preset || preset.paint_id === 0) {
            return {
                available: true,
                paint_id: 0,
                name: 'Padrão / Vanilla',
                image_url: knife.image_url
            };
        }

        // Resolver se esta faca usa um Paint ID alternativo da Valve para este preset
        let targetPid = preset.paint_id;
        if (PRESET_ALIASES[preset.paint_id] && PRESET_ALIASES[preset.paint_id][knife.model]) {
            targetPid = PRESET_ALIASES[preset.paint_id][knife.model];
        }

        const pidStr = String(targetPid);
        if (knife.skins_by_paint && knife.skins_by_paint[pidStr]) {
            const officialSkin = knife.skins_by_paint[pidStr];
            return {
                available: true,
                paint_id: targetPid,
                name: preset.name,
                image_url: officialSkin.image_url
            };
        }

        // A faca realmente não possui esse acabamento no CS2 oficial da Valve (ex: Kukri e Classic em Doppler)
        return {
            available: false,
            paint_id: 0,
            name: `${preset.name} (Inexistente no CS2)`,
            image_url: knife.image_url
        };
    }

    function getPresetBadgeColor(cssClass) {
        switch (cssClass) {
            case 'ruby': return '#e63946';
            case 'sapphire': return '#2b70e4';
            case 'blackpearl': return '#6441a5';
            case 'emerald': return '#10b981';
            case 'fade': return '#d32ce6';
            case 'bluegem': return '#00d2ff';
            case 'tiger': return '#ff8c00';
            case 'crimson': return '#8b0000';
            case 'slaughter': return '#e60039';
            case 'lore': return '#b8860b';
            case 'autotronic': return '#e63946';
            default: return 'var(--accent-gold)';
        }
    }

    // =========================================================================
    // Weapon Filter Pills (Subcategorias de Armas)
    // =========================================================================
    function renderWeaponPills() {
        if (!state.catalog || !state.catalog.weapons) return;
        weaponPillsBar.innerHTML = '';

        let targetWeapons = state.catalog.weapons;
        if (state.activeTab === 'rifles') {
            targetWeapons = targetWeapons.filter(w => ['rifle', 'sniper'].includes(w.category));
        } else if (state.activeTab === 'pistols') {
            targetWeapons = targetWeapons.filter(w => ['pistol', 'smg', 'heavy'].includes(w.category));
        }

        // 1. Pílula "TODAS"
        const totalCount = targetWeapons.reduce((sum, w) => sum + (w.skins ? w.skins.length : 0), 0);
        const allPill = document.createElement('div');
        allPill.className = `weapon-pill ${state.selectedWeaponFilter === 'ALL' ? 'active' : ''}`;
        allPill.innerHTML = `Todas as Armas (${totalCount})`;
        allPill.addEventListener('click', () => {
            state.selectedWeaponFilter = 'ALL';
            syncTeamRestrictions('ALL');
            renderWeaponPills();
            renderGrid();
        });
        weaponPillsBar.appendChild(allPill);

        // 2. Pílulas de cada arma específica
        targetWeapons.forEach(w => {
            const count = w.skins ? w.skins.length : 0;
            const pill = document.createElement('div');
            const isActive = state.selectedWeaponFilter === w.weapon_key;
            pill.className = `weapon-pill ${isActive ? 'active' : ''}`;
            pill.innerHTML = `${w.name} (${count})`;
            pill.addEventListener('click', () => {
                state.selectedWeaponFilter = w.weapon_key;
                syncTeamRestrictions(w.weapon_key);
                renderWeaponPills();
                renderGrid();
            });
            weaponPillsBar.appendChild(pill);
        });
    }

    // =========================================================================
    // Grid Principal de Itens
    // =========================================================================
    function renderGrid() {
        itemsGrid.innerHTML = '';
        if (!state.catalog) return;

        if (state.activeTab === 'knives') {
            if (knifeSkinSelectGroup) knifeSkinSelectGroup.style.display = 'block';
            let knives = state.catalog.knives || [];
            if (state.searchQuery) {
                knives = knives.filter(k => k.name.toLowerCase().includes(state.searchQuery));
            }
            renderKnivesList(knives);
        } else {
            if (knifeSkinSelectGroup) knifeSkinSelectGroup.style.display = 'none';

            if (state.activeTab === 'gloves') {
                let gloves = state.catalog.gloves || [];
                if (state.searchQuery) {
                    gloves = gloves.filter(g => g.name.toLowerCase().includes(state.searchQuery));
                }
                renderGlovesList(gloves);
            } else if (state.activeTab === 'rifles' || state.activeTab === 'pistols') {
                let weapons = state.catalog.weapons || [];
                if (state.activeTab === 'rifles') {
                    weapons = weapons.filter(w => ['rifle', 'sniper'].includes(w.category));
                } else {
                    weapons = weapons.filter(w => ['pistol', 'smg', 'heavy'].includes(w.category));
                }
                renderWeaponsList(weapons);
            } else if (state.activeTab === 'inventory') {
                renderInventoryList();
            }
        }
    }

    // =========================================================================
    // Renderização de Facas (com Troca Global de Acabamento)
    // =========================================================================
    function renderKnivesList(knives) {
        if (knives.length === 0) {
            itemsGrid.innerHTML = '<div style="color: var(--text-muted); padding: 20px;">Nenhuma faca encontrada para essa busca.</div>';
            return;
        }

        knives.forEach(knife => {
            const card = document.createElement('div');

            // Determinar a skin e a foto exibida com base no preset de gema global ativo
            const skinInfo = getKnifeSkinForPreset(knife, state.selectedGemPreset);
            const isEquipped = checkIfKnifeEquipped(knife.model);

            let badgeHtml = '';
            let cardExtraClass = '';
            let footerHtml = '';
            let displayName = knife.name;

            if (state.selectedGemPreset && state.selectedGemPreset.paint_id > 0) {
                if (skinInfo.available) {
                    const badgeText = state.selectedGemPreset.badge || state.selectedGemPreset.name;
                    badgeHtml = `<span class="card-gem-badge ${state.selectedGemPreset.css_class}">${badgeText}</span>`;
                    displayName = `${knife.name} | ${skinInfo.name}`;
                    footerHtml = `
                        <span>Paint: ${skinInfo.paint_id}</span>
                        <span style="color: var(--accent-gold);">★ Especial Raro</span>
                    `;
                } else {
                    badgeHtml = `<span class="card-gem-badge unavailable">NÃO DISPONÍVEL NO CS2</span>`;
                    cardExtraClass = 'skin-unavailable';
                    displayName = `${knife.name}`;
                    footerHtml = `
                        <span style="color: var(--text-muted);">Inexistente no CS2</span>
                        <span style="color: #6b7280;">Sem Doppler</span>
                    `;
                }
            } else {
                footerHtml = `
                    <span>Padrão de Fábrica</span>
                    <span style="color: var(--accent-gold);">★ Especial Raro</span>
                `;
            }

            let equippedHtml = isEquipped ? `<span class="card-equipped-tag">EQUIPADO</span>` : '';

            card.className = `item-card ${cardExtraClass}`;
            card.innerHTML = `
                ${badgeHtml}
                ${equippedHtml}
                <div class="card-weapon-type">FACA CORPO-A-CORPO</div>
                <div class="card-skin-name">${displayName}</div>
                <div class="card-image-wrapper">
                    <img src="${skinInfo.image_url}" alt="${displayName}" loading="lazy" onerror="this.src='${knife.image_url}'">
                </div>
                <div class="card-footer">
                    ${footerHtml}
                </div>
            `;

            card.addEventListener('click', () => {
                selectKnife(knife, skinInfo);
            });

            itemsGrid.appendChild(card);
        });

        // Se nenhum item selecionado ainda, seleciona a primeira faca
        if (!state.selectedItem || state.selectedItem.type !== 'knife') {
            const firstKnife = knives[0];
            const firstSkin = getKnifeSkinForPreset(firstKnife, state.selectedGemPreset);
            selectKnife(firstKnife, firstSkin);
        }
    }

    function selectKnife(knife, skinInfo) {
        state.selectedItem = {
            type: 'knife',
            knife: knife,
            name: knife.name,
            model: knife.model,
            defindex: knife.defindex,
            image_url: skinInfo ? skinInfo.image_url : knife.image_url,
            currentSkin: skinInfo
        };

        inspectImage.src = state.selectedItem.image_url;

        if (skinInfo && skinInfo.available && skinInfo.paint_id > 0) {
            inspectName.textContent = `${knife.name} | ${skinInfo.name}`;
            inspectType.textContent = `Acabamento Oficial (Paint ID: ${skinInfo.paint_id})`;
            paintIdInput.value = skinInfo.paint_id;
            inspectRarity.textContent = '★ EXTRAORDINÁRIO';
            inspectRarity.style.background = 'var(--accent-gold)';
            inspectRarity.style.color = '#000';
        } else if (skinInfo && !skinInfo.available) {
            inspectName.textContent = `${knife.name} (Vanilla)`;
            inspectType.textContent = 'A Valve nunca lançou caixas com acabamento Doppler para este modelo no CS2';
            paintIdInput.value = 0;
            inspectRarity.textContent = '★ SEM VERSÃO NO JOGO';
            inspectRarity.style.background = '#4b5563';
            inspectRarity.style.color = '#d1d5db';
        } else {
            inspectName.textContent = knife.name;
            inspectType.textContent = 'Faca / Especial Raro (Padrão Vanilla)';
            paintIdInput.value = 0;
            inspectRarity.textContent = '★ EXTRAORDINÁRIO';
            inspectRarity.style.background = 'var(--accent-gold)';
            inspectRarity.style.color = '#000';
        }

        // Popular o dropdown de pinturas individuais para essa faca
        populateKnifeSkinDropdown(knife, skinInfo);

        // Destacar card selecionado
        document.querySelectorAll('.item-card').forEach(c => c.classList.remove('selected'));

        // Facas são utilizáveis por ambos os lados
        syncTeamRestrictions(null);
    }

    function populateKnifeSkinDropdown(knife, currentSkin) {
        if (!knifeSkinSelect) return;
        knifeSkinSelect.innerHTML = '';

        // Opção Vanilla
        const optVanilla = document.createElement('option');
        optVanilla.value = '0';
        optVanilla.textContent = '★ Acabamento Vanilla (Padrão de Fábrica)';
        knifeSkinSelect.appendChild(optVanilla);

        // Todas as skins oficiais da faca
        const skins = knife.skins || [];
        skins.forEach(s => {
            const opt = document.createElement('option');
            opt.value = String(s.paint_id);
            opt.textContent = `${s.name} (Paint ID: ${s.paint_id})`;
            if (currentSkin && String(currentSkin.paint_id) === String(s.paint_id)) {
                opt.selected = true;
            }
            knifeSkinSelect.appendChild(opt);
        });

        if (currentSkin && currentSkin.paint_id === 0) {
            optVanilla.selected = true;
        }
    }

    function handleIndividualKnifeSkinChange(paintIdStr) {
        if (!state.selectedItem || state.selectedItem.type !== 'knife') return;

        const knife = state.selectedItem.knife;
        const pid = parseInt(paintIdStr, 10);

        let chosenSkin = null;
        if (pid === 0) {
            chosenSkin = { paint_id: 0, name: 'Padrão / Vanilla', image_url: knife.image_url };
        } else if (knife.skins_by_paint && knife.skins_by_paint[paintIdStr]) {
            chosenSkin = knife.skins_by_paint[paintIdStr];
        } else {
            chosenSkin = { paint_id: pid, name: `Paint ${pid}`, image_url: knife.image_url };
        }

        state.selectedItem.image_url = chosenSkin.image_url;
        state.selectedItem.currentSkin = chosenSkin;

        inspectImage.src = chosenSkin.image_url;
        inspectName.textContent = pid > 0 ? `${knife.name} | ${chosenSkin.name}` : knife.name;
        inspectType.textContent = `Acabamento Selecionado (Paint ${pid})`;
        paintIdInput.value = pid;

        showToast(`Pintura ${chosenSkin.name} selecionada para ${knife.name}!`, '🗡️');
    }

    // =========================================================================
    // Renderização de Luvas
    // =========================================================================
    function renderGlovesList(gloves) {
        if (gloves.length === 0) {
            itemsGrid.innerHTML = '<div style="color: var(--text-muted); padding: 20px;">Nenhuma luva encontrada para essa busca.</div>';
            return;
        }

        gloves.forEach(glove => {
            const card = document.createElement('div');
            card.className = 'item-card';

            const isEquipped = checkIfGloveEquipped(glove.defindex);
            let equippedHtml = isEquipped ? `<span class="card-equipped-tag">EQUIPADO</span>` : '';

            card.innerHTML = `
                ${equippedHtml}
                <div class="card-weapon-type">LUVAS</div>
                <div class="card-skin-name">${glove.name}</div>
                <div class="card-image-wrapper">
                    <img src="${glove.image_url}" alt="${glove.name}" loading="lazy">
                </div>
                <div class="card-footer">
                    <span>Paint: ${glove.paint_id}</span>
                    <span style="color: #d32ce6;">★ Luvas</span>
                </div>
            `;

            card.addEventListener('click', () => {
                selectGlove(glove);
            });

            itemsGrid.appendChild(card);
        });

        if (!state.selectedItem || state.selectedItem.type !== 'glove') {
            selectGlove(gloves[0]);
        }
    }

    function selectGlove(glove) {
        state.selectedItem = {
            type: 'glove',
            name: glove.name,
            defindex: glove.defindex,
            paint_id: glove.paint_id,
            image_url: glove.image_url
        };

        inspectImage.src = glove.image_url;
        inspectName.textContent = glove.name;
        inspectType.textContent = `Luvas de Operação (DefIndex: ${glove.defindex})`;
        inspectRarity.textContent = '★ EXTRAORDINÁRIO';
        inspectRarity.style.background = '#d32ce6';
        inspectRarity.style.color = '#fff';

        paintIdInput.value = glove.paint_id;

        // Luvas são utilizáveis por ambos os lados
        syncTeamRestrictions(null);
    }

    // =========================================================================
    // Renderização de Armas (TODAS AS SKINS SEM LIMITE)
    // =========================================================================
    function renderWeaponsList(weapons) {
        // Se houver um filtro de arma selecionado (ex: AK-47)
        if (state.selectedWeaponFilter !== 'ALL') {
            weapons = weapons.filter(w => w.weapon_key === state.selectedWeaponFilter);
        }

        let totalCardsRendered = 0;

        weapons.forEach(weapon => {
            let skinsToShow = weapon.skins || [];

            // Se o usuário digitou algo na busca, filtra por nome da skin ou arma
            if (state.searchQuery) {
                if (!weapon.name.toLowerCase().includes(state.searchQuery)) {
                    skinsToShow = skinsToShow.filter(s => s.name.toLowerCase().includes(state.searchQuery));
                }
            }

            // Exibir todas as skins da arma
            skinsToShow.forEach(skin => {
                totalCardsRendered++;
                const card = document.createElement('div');
                card.className = 'item-card';

                const isEquipped = checkIfSkinEquipped(weapon.defindex, skin.paint_id);
                let equippedHtml = isEquipped ? `<span class="card-equipped-tag">EQUIPADO</span>` : '';

                card.innerHTML = `
                    ${equippedHtml}
                    <div class="card-weapon-type">${weapon.name}</div>
                    <div class="card-skin-name">${skin.name}</div>
                    <div class="card-image-wrapper">
                        <img src="${skin.image_url}" alt="${weapon.name} ${skin.name}" loading="lazy">
                    </div>
                    <div class="card-footer">
                        <span>Paint: ${skin.paint_id}</span>
                        <span style="color: #eb4b4b;">Secreto</span>
                    </div>
                `;

                card.addEventListener('click', () => {
                    selectWeaponSkin(weapon, skin);
                });

                itemsGrid.appendChild(card);
            });
        });

        if (totalCardsRendered === 0) {
            itemsGrid.innerHTML = '<div style="color: var(--text-muted); padding: 20px;">Nenhuma skin encontrada para este filtro. Experimente buscar por outro nome ou selecionar outra arma.</div>';
        }
    }

    function selectWeaponSkin(weapon, skin) {
        state.selectedItem = {
            type: 'weapon',
            weapon: weapon,
            skin: skin,
            name: `${weapon.name} | ${skin.name}`,
            image_url: skin.image_url
        };

        inspectImage.src = skin.image_url;
        inspectName.textContent = `${weapon.name} | ${skin.name}`;
        inspectType.textContent = `${weapon.name} (Paint ID: ${skin.paint_id})`;
        inspectRarity.textContent = 'SECRETO';
        inspectRarity.style.background = '#eb4b4b';
        inspectRarity.style.color = '#fff';

        paintIdInput.value = skin.paint_id;

        // Sincronizar restrição de equipe oficial (ex: AK-47 -> TR, M4A1-S -> CT)
        syncTeamRestrictions(weapon.weapon_key);
    }

    // =========================================================================
    // Inventário do Jogador (Cards Visuais Ricos)
    // =========================================================================
    function renderInventoryList() {
        itemsGrid.innerHTML = '';
        if (!state.inventory) {
            itemsGrid.innerHTML = '<div style="color: var(--text-muted); padding: 20px;">Carregando inventário...</div>';
            return;
        }

        let items = state.inventory.equipped_items || [];

        // 1. Filtrar por equipe ativa: CT (3) ou TR (2) ou AMBOS (0)
        if (state.activeTeam === 3) {
            items = items.filter(item => item.team === 3 || item.team === 0);
        } else if (state.activeTeam === 2) {
            items = items.filter(item => item.team === 2 || item.team === 0);
        }

        // 2. Filtrar por texto de busca (searchQuery) se o usuário digitou algo
        if (state.searchQuery) {
            items = items.filter(item => {
                const q = state.searchQuery.toLowerCase();
                const matchFull = item.full_name && item.full_name.toLowerCase().includes(q);
                const matchWeapon = item.weapon_name && item.weapon_name.toLowerCase().includes(q);
                const matchSkin = item.skin_name && item.skin_name.toLowerCase().includes(q);
                const matchNametag = item.nametag && item.nametag.toLowerCase().includes(q);
                return matchFull || matchWeapon || matchSkin || matchNametag;
            });
        }

        if (items.length === 0) {
            let filterDesc = '';
            if (state.activeTeam === 3) filterDesc = ' para os Contraterroristas (CT)';
            else if (state.activeTeam === 2) filterDesc = ' para os Terroristas (TR)';

            itemsGrid.innerHTML = `
                <div class="inventory-empty-state">
                    <div class="empty-icon">🎒</div>
                    <h3>Nenhum Item Equipado Encontrado${filterDesc}</h3>
                    <p>Não há cosméticos equipados correspondentes aos filtros selecionados. Clique em "AMBOS" para ver todos os itens ou navegue pelo catálogo para equipar skins nesta equipe!</p>
                </div>
            `;
            return;
        }

        items.forEach(item => {
            const card = document.createElement('div');
            card.className = 'item-card';

            // Tag do Time (CT / TR / AMBOS)
            let teamClass = 'both';
            let teamLabel = 'AMBOS';
            if (item.team === 3) {
                teamClass = 'ct';
                teamLabel = 'CT';
            } else if (item.team === 2) {
                teamClass = 'tr';
                teamLabel = 'TR';
            }
            const teamBadgeHtml = `<span class="card-team-badge ${teamClass}">EQUIPE ${teamLabel}</span>`;

            // Badge StatTrak
            let statTrakHtml = '';
            if (item.stattrak) {
                statTrakHtml = `<span class="card-stattrak-badge">StatTrak™ (${item.stattrak_count})</span>`;
            }

            // Badge NameTag
            let nametagHtml = '';
            if (item.nametag) {
                nametagHtml = `<span class="card-nametag-badge" title="${item.nametag}">🏷️ ${item.nametag}</span>`;
            }

            // Tipo e Cor do Rodapé
            let typeLabel = 'ARMA';
            let footerColor = '#eb4b4b';
            let rarityLabel = 'Secreto';

            if (item.type === 'knife') {
                typeLabel = 'FACA CORPO-A-CORPO';
                footerColor = 'var(--accent-gold)';
                rarityLabel = '★ Especial Raro';
            } else if (item.type === 'glove') {
                typeLabel = 'LUVAS';
                footerColor = '#d32ce6';
                rarityLabel = '★ Luvas';
            }

            // Float Wear Condition
            const wearVal = parseFloat(item.wear) || 0.0001;
            let wearCondition = 'FN';
            if (wearVal >= 0.45) wearCondition = 'BS';
            else if (wearVal >= 0.38) wearCondition = 'WW';
            else if (wearVal >= 0.15) wearCondition = 'FT';
            else if (wearVal >= 0.07) wearCondition = 'MW';

            const imageHtml = item.image_url ? 
                `<img src="${item.image_url}" alt="${item.full_name}" loading="lazy" onerror="this.style.display='none'">` :
                `<div style="font-size: 32px; color: var(--text-muted); opacity: 0.3;">📦</div>`;

            card.innerHTML = `
                ${teamBadgeHtml}
                <div class="card-weapon-type">${typeLabel}</div>
                <div class="card-skin-name">${item.full_name || item.weapon_name}</div>
                <div class="card-image-wrapper">
                    ${imageHtml}
                </div>
                ${nametagHtml}
                ${statTrakHtml}
                <div class="card-footer">
                    <span>Float: ${wearVal.toFixed(4)} (${wearCondition})</span>
                    <span style="color: ${footerColor};">${rarityLabel}</span>
                </div>
            `;

            // Ao clicar, inspeciona o item equipado no drawer lateral
            card.addEventListener('click', () => {
                inspectEquippedItem(item);
            });

            itemsGrid.appendChild(card);
        });

        // Se nenhum item estiver no drawer lateral, inspeciona o primeiro
        if (items.length > 0 && (!state.selectedItem || state.selectedItem.fromInventory)) {
            inspectEquippedItem(items[0]);
        }
    }

    function inspectEquippedItem(item) {
        state.selectedItem = {
            type: item.type,
            fromInventory: true,
            model: item.model,
            defindex: item.defindex,
            weapon_name: item.weapon_name,
            name: item.full_name,
            image_url: item.image_url,
            weapon: { defindex: item.defindex, name: item.weapon_name }
        };

        inspectImage.src = item.image_url;
        inspectName.textContent = item.full_name;
        inspectType.textContent = `Equipado para ${item.team === 3 ? 'Contraterroristas (CT)' : item.team === 2 ? 'Terroristas (TR)' : 'Ambos os Times'}`;
        
        if (item.type === 'knife') {
            inspectRarity.textContent = '★ EXTRAORDINÁRIO';
            inspectRarity.style.background = 'var(--accent-gold)';
            inspectRarity.style.color = '#000';
        } else if (item.type === 'glove') {
            inspectRarity.textContent = '★ EXTRAORDINÁRIO';
            inspectRarity.style.background = '#d32ce6';
            inspectRarity.style.color = '#fff';
        } else {
            inspectRarity.textContent = 'SECRETO';
            inspectRarity.style.background = '#eb4b4b';
            inspectRarity.style.color = '#fff';
        }

        paintIdInput.value = item.paint_id || 0;
        seedInput.value = item.seed || 0;
        floatSlider.value = item.wear || 0.0001;
        updateFloatDisplay(item.wear || 0.0001);
        nametagInput.value = item.nametag || '';
        stattrakCheckbox.checked = !!item.stattrak;
        stattrakCountInput.value = item.stattrak_count || 0;

        document.querySelectorAll('.item-card').forEach(c => c.classList.remove('selected'));
    }

    // =========================================================================
    // Salvar / Equipar Itens no MariaDB
    // =========================================================================
    async function equipSelectedItem() {
        if (!state.selectedItem) {
            showToast('Selecione um item primeiro no catálogo!', '⚠️');
            return;
        }

        const steamid = state.currentSteamId;
        const team = state.activeTeam; // 0, 2, ou 3
        const floatVal = parseFloat(floatSlider.value) || 0.0001;
        const seedVal = parseInt(seedInput.value, 10) || 0;
        const paintVal = parseInt(paintIdInput.value, 10) || 0;
        const nametagVal = nametagInput.value.trim();
        const stattrakVal = stattrakCheckbox.checked;
        const stattrakCount = parseInt(stattrakCountInput.value, 10) || 0;

        try {
            if (state.selectedItem.type === 'knife') {
                const knifeDefindex = state.selectedItem.defindex || 507;

                // 1. Salvar modelo de faca e pintura via API
                const knifeRes = await fetch('/api/equip/knife', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        steamid: steamid,
                        knife: state.selectedItem.model,
                        defindex: knifeDefindex,
                        paint_id: paintVal,
                        wear: floatVal,
                        seed: seedVal,
                        nametag: nametagVal,
                        stattrak: stattrakVal,
                        stattrak_count: stattrakCount,
                        team: team
                    })
                });
                const knifeJson = await knifeRes.json();
                if (!knifeJson.success) throw new Error(knifeJson.message);

                showToast(`Faca ${state.selectedItem.name} equipada com sucesso! Digite !wp no jogo.`, '🗡️');
            } else if (state.selectedItem.type === 'glove') {
                const gloveRes = await fetch('/api/equip/gloves', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        steamid: steamid,
                        defindex: state.selectedItem.defindex,
                        paint_id: paintVal || state.selectedItem.paint_id,
                        wear: floatVal,
                        seed: seedVal,
                        team: team
                    })
                });
                const gloveJson = await gloveRes.json();
                if (!gloveJson.success) throw new Error(gloveJson.message);

                showToast(`Luvas equipadas com sucesso! Digite !wp no jogo.`, '🧤');
            } else if (state.selectedItem.type === 'weapon') {
                const skinRes = await fetch('/api/equip/skin', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        steamid: steamid,
                        defindex: state.selectedItem.weapon.defindex,
                        paint_id: paintVal,
                        wear: floatVal,
                        seed: seedVal,
                        nametag: nametagVal,
                        stattrak: stattrakVal,
                        stattrak_count: stattrakCount,
                        team: team
                    })
                });
                const skinJson = await skinRes.json();
                if (!skinJson.success) throw new Error(skinJson.message);

                showToast(`Skin ${state.selectedItem.name} equipada com sucesso! Digite !wp no jogo.`, '🔫');
            }

            // Recarregar inventário e re-renderizar
            await fetchInventory();
            renderGrid();
        } catch (err) {
            console.error('Erro ao equipar item:', err);
            showToast(`Erro ao salvar no banco: ${err.message}`, '❌');
        }
    }

    function checkIfKnifeEquipped(model) {
        if (!state.inventory || !state.inventory.knives) return false;
        return state.inventory.knives.some(k => k.knife === model);
    }

    function checkIfGloveEquipped(defindex) {
        if (!state.inventory || !state.inventory.gloves) return false;
        return state.inventory.gloves.some(g => g.defindex === defindex);
    }

    function checkIfSkinEquipped(defindex, paintId) {
        if (!state.inventory || !state.inventory.skins) return false;
        return state.inventory.skins.some(s => s.defindex === defindex && s.paint_id === paintId);
    }

    function showToast(msg, icon = '✨') {
        const toast = document.createElement('div');
        toast.className = 'toast';
        toast.innerHTML = `
            <div class="toast-icon">${icon}</div>
            <div class="toast-msg">
                <h4>Arsenal Web UI</h4>
                <p>${msg}</p>
            </div>
        `;

        toastContainer.appendChild(toast);

        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transform = 'translateX(100%)';
            setTimeout(() => toast.remove(), 300);
        }, 4000);
    }

    // =========================================================================
    // Funções de Inspeção 3D e Integração CS2
    // =========================================================================
    function setupStageInteractions() {
        if (!inspectStage) return;

        // Mouse Drag / Tilt
        inspectStage.addEventListener('mousedown', (e) => {
            if (e.target.closest('.stage-controls')) return;
            isDraggingStage = true;
            dragStartX = e.clientX;
            dragStartY = e.clientY;
            if (isAutoRotating) {
                toggleAutoRotate(false);
            }
        });

        window.addEventListener('mousemove', (e) => {
            if (isDraggingStage) {
                const dx = e.clientX - dragStartX;
                const dy = e.clientY - dragStartY;
                inspectRotationY += dx * 0.45;
                inspectRotationX = Math.max(-45, Math.min(45, inspectRotationX - dy * 0.45));
                dragStartX = e.clientX;
                dragStartY = e.clientY;
                applyStageTransform();
            } else if (inspectModalBackdrop && inspectModalBackdrop.style.display !== 'none' && !isAutoRotating) {
                const rect = inspectStage.getBoundingClientRect();
                if (e.clientX >= rect.left && e.clientX <= rect.right &&
                    e.clientY >= rect.top && e.clientY <= rect.bottom) {
                    const relX = (e.clientX - rect.left) / rect.width - 0.5;
                    const relY = (e.clientY - rect.top) / rect.height - 0.5;
                    inspectRotationY = relX * 35;
                    inspectRotationX = -relY * 25;
                    applyStageTransform();
                    if (stageReflection) {
                        stageReflection.style.transform = `translate(${relX * 60}px, ${relY * 60}px)`;
                        stageReflection.style.opacity = `${Math.abs(relX) * 0.6 + 0.2}`;
                    }
                }
            }
        });

        window.addEventListener('mouseup', () => {
            isDraggingStage = false;
        });

        // Controles de Giro e Visualização
        if (btnToggleRotate) {
            btnToggleRotate.addEventListener('click', () => {
                toggleAutoRotate(!isAutoRotating);
            });
        }

        if (btnFlipSide) {
            btnFlipSide.addEventListener('click', () => {
                inspectScaleX = inspectScaleX === 1 ? -1 : 1;
                applyStageTransform();
                showToast(inspectScaleX === 1 ? 'Exibindo Playside (Frente)' : 'Exibindo Backside (Verso)', '↔️');
            });
        }

        if (btnResetView) {
            btnResetView.addEventListener('click', () => {
                resetStageView();
            });
        }

        // Ações de Disparo
        if (btnLaunchCs2Inspect) {
            btnLaunchCs2Inspect.addEventListener('click', () => {
                if (currentInspectData && currentInspectData.steam_link) {
                    window.location.href = currentInspectData.steam_link;
                    showToast('Abrindo tela de inspeção oficial no CS2...', '🎮');
                } else {
                    showToast('Link de inspeção indisponível para este item.', '⚠️');
                }
            });
        }

        if (btnCopyInspectLink) {
            btnCopyInspectLink.addEventListener('click', async () => {
                if (currentInspectData && currentInspectData.steam_link) {
                    try {
                        await navigator.clipboard.writeText(currentInspectData.steam_link);
                        showToast('Link da Steam copiado para a área de transferência!', '📋');
                    } catch {
                        prompt('Copie o link da Steam:', currentInspectData.steam_link);
                    }
                }
            });
        }

        if (btnCopyConsoleCmd) {
            btnCopyConsoleCmd.addEventListener('click', async () => {
                if (currentInspectData && currentInspectData.console_cmd) {
                    try {
                        await navigator.clipboard.writeText(currentInspectData.console_cmd);
                        showToast('Comando de console copiado! Cole no console do CS2 (~).', '⌨️');
                    } catch {
                        prompt('Copie o comando de console:', currentInspectData.console_cmd);
                    }
                }
            });
        }

        if (btnOpenWeb3D) {
            btnOpenWeb3D.addEventListener('click', () => {
                if (currentInspectData && currentInspectData.web_3d_url) {
                    window.open(currentInspectData.web_3d_url, '_blank');
                    showToast('Abrindo visualizador 3D online no navegador...', '🌐');
                }
            });
        }
    }

    function applyStageTransform() {
        if (!stageTurntable) return;
        stageTurntable.style.transform = `rotateX(${inspectRotationX}deg) rotateY(${inspectRotationY * inspectScaleX}deg) scaleX(${inspectScaleX})`;
    }

    function toggleAutoRotate(enable) {
        isAutoRotating = enable;
        if (btnToggleRotate) {
            btnToggleRotate.classList.toggle('active', isAutoRotating);
        }
        if (isAutoRotating) {
            function loop() {
                if (!isAutoRotating) return;
                inspectRotationY = (inspectRotationY + 1.2) % 360;
                applyStageTransform();
                autoRotateAnimId = requestAnimationFrame(loop);
            }
            loop();
        } else if (autoRotateAnimId) {
            cancelAnimationFrame(autoRotateAnimId);
            autoRotateAnimId = null;
        }
    }

    function resetStageView() {
        toggleAutoRotate(false);
        inspectRotationY = 0;
        inspectRotationX = 0;
        inspectScaleX = 1;
        applyStageTransform();
        if (stageReflection) {
            stageReflection.style.transform = 'translate(0px, 0px)';
            stageReflection.style.opacity = '0.4';
        }
    }

    async function openInspectModal() {
        if (!state.selectedItem) {
            showToast('Selecione um item primeiro no catálogo!', '⚠️');
            return;
        }

        const floatVal = parseFloat(floatSlider.value) || 0.0001;
        const seedVal = parseInt(seedInput.value, 10) || 0;
        const paintVal = parseInt(paintIdInput.value, 10) || 0;
        const nametagVal = nametagInput.value.trim();
        const stattrakVal = stattrakCheckbox.checked;
        const stattrakCount = parseInt(stattrakCountInput.value, 10) || 0;

        let defindex = 7;
        let itemName = 'Arma';
        let itemType = 'Arma de Fogo';
        let imgUrl = inspectImage.src;
        let rarityBadge = 'SECRETO';
        let rarityBg = '#eb4b4b';

        if (state.selectedItem.type === 'knife') {
            defindex = state.selectedItem.defindex || state.selectedItem.knife?.defindex || 507;
            itemName = state.selectedItem.name || 'Faca';
            itemType = 'Faca Corpo-a-Corpo';
            rarityBadge = 'EXTRAORDINÁRIO';
            rarityBg = '#e5a93c';
        } else if (state.selectedItem.type === 'glove') {
            defindex = state.selectedItem.defindex || 5030;
            itemName = state.selectedItem.name || 'Luvas';
            itemType = 'Luvas Táticas';
            rarityBadge = 'EXTRAORDINÁRIO';
            rarityBg = '#e5a93c';
        } else if (state.selectedItem.type === 'weapon') {
            defindex = state.selectedItem.weapon?.defindex || state.selectedItem.defindex || 7;
            itemName = `${state.selectedItem.weapon?.name || ''} | ${state.selectedItem.name}`;
            itemType = state.selectedItem.weapon?.category?.toUpperCase() || 'ARMA';
            rarityBadge = 'SECRETO';
            rarityBg = '#eb4b4b';
        }

        // Preencher Dados no Modal
        modalWeaponName.textContent = itemName;
        modalWeaponType.textContent = itemType;
        modalRarityBadge.textContent = rarityBadge;
        modalRarityBadge.style.backgroundColor = rarityBg;
        modalInspectImage.src = imgUrl;

        modalFloatVal.textContent = `${floatVal.toFixed(4)} (${getConditionText(floatVal)})`;
        modalSeedVal.textContent = `${seedVal}`;
        modalPaintVal.textContent = `${paintVal}`;

        if (stattrakVal) {
            modalStattrakBox.style.display = 'flex';
            modalStattrakVal.textContent = `${stattrakCount} Kills`;
        } else {
            modalStattrakBox.style.display = 'none';
        }

        if (nametagVal) {
            modalNametagBox.style.display = 'flex';
            modalNametagVal.textContent = `"${nametagVal}"`;
        } else {
            modalNametagBox.style.display = 'none';
        }

        resetStageView();

        // Buscar Payload da API
        try {
            const res = await fetch('/api/inspect-link', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    defindex: defindex,
                    paint_id: paintVal,
                    wear: floatVal,
                    seed: seedVal,
                    stattrak: stattrakVal,
                    stattrak_count: stattrakCount,
                    nametag: nametagVal,
                    rarity: defindex >= 500 ? 6 : 5
                })
            });
            currentInspectData = await res.json();
        } catch (e) {
            console.error('Erro ao gerar inspect link:', e);
            currentInspectData = null;
        }

        inspectModalBackdrop.style.display = 'flex';
    }

    function closeInspectModal() {
        toggleAutoRotate(false);
        inspectModalBackdrop.style.display = 'none';
    }
});