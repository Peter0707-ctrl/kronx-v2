# Copetra-v1 Model Training and Deployment Guide

Mwongozo rasmi wa kufundisha na kuzalisha modeli yetu ya **Copetra-v1 (7B Parameters)** kwa kutumia Google Colab (NVIDIA T4 GPU ya bure) na kuiweka hewani kwenye seva yetu ya nje.

---

## 1. Yaliyomo Katika Folda Hii (`training/`)

- **`copetra_dataset_v1.jsonl`**: Faili la data za mafunzo (Instruction-Tuning Dataset) lenye maswali na majibu ya kiwango cha Claude / ChatGPT kwa lugha ya Kiswahili na Kiingereza, likiwa na staha, hisia, hesabu, na kodi bila emojis wala marudio.
- **`build_dataset.py`**: Skripti ya Python inayopanua na kuzalisha data mpya za mafunzo.
- **`train_copetra_colab.py`**: Skripti kamili ya Google Colab inayotumia maktaba ya **Unsloth** na **QLoRA** kufundisha modeli msingi ya `Qwen2.5-7B` au `Llama-3.1-8B` kwa dakika 45 hadi saa 1 kwenye GPU ya bure.
- **`Modelfile`**: Faili la kusanidi modeli yetu kwenye injini ya Ollama ili iweze kujibu kama **Copetra AI (PJ COPETRANOVA)**.

---

## 2. Jinsi ya Kufundisha Kwenye Google Colab (Bure):

### Hatua ya 1: Fungua Google Colab
1. Nenda kwenye kivinjari chako: `https://colab.research.google.com`
2. Bofya **New Notebook**.
3. Kwenye menyu ya juu, bofya **Runtime** -> **Change runtime type**.
4. Chagua **T4 GPU** chini ya *Hardware accelerator*, kisha bofya **Save**.

### Hatua ya 2: Pakia Data na Skripti
1. Upande wa kushoto wa Google Colab, bofya aikoni ya jalada (Folder icon).
2. Buruta (drag and drop) faili hizi mbili kutoka kwenye kompyuta yako:
   - `training/copetra_dataset_v1.jsonl`
   - `training/train_copetra_colab.py`

### Hatua ya 3: Endesha Mafunzo
Kwenye kisanduku cha kwanza cha Colab (code cell), andika amri hii kisha ubonyeze kitufe cha kuendesha (Play):

```bash
!python train_copetra_colab.py
```

Mfumo utaanza moja kwa moja:
1. Kupakua Unsloth na utegemezi wake.
2. Kupakia ubongo wa `Qwen2.5-7B-Instruct`.
3. Kufundisha maadili na lugha ya Copetra kwa kutumia GPU.
4. Kuzalisha faili jipya lililokamilika la: **`copetra-v1-7b-unsloth.Q4_K_M.gguf`** (takriban GB 4.5).

### Hatua ya 4: Pakua Faili Lako la Modeli
- Baada ya mafunzo kukamilika, bofya kulia faili la `copetra-v1-7b-unsloth.Q4_K_M.gguf` kwenye Colab na uchague **Download** (au lihifadhi moja kwa moja kwenye Google Drive yako).
- Hili ndilo faili rasmi la ubongo wetu linalomilikiwa na **PJ COPETRANOVA / Copetra AI**.

---

## 3. Jinsi ya Kuiweka Hewani Kwenye Seva ya Nje ($10 - $15/mwezi):

1. Kwenye seva ya nje (k.m. Hetzner Cloud yenye Ubuntu 24.04 na GB 16 RAM), weka Ollama:
   ```bash
   curl -fsSL https://ollama.com/install.sh | sh
   ```
2. Hamisha faili la `copetra-v1-7b-unsloth.Q4_K_M.gguf` na `Modelfile` kwenye seva hiyo.
3. Tengeneza modeli rasmi ya Copetra:
   ```bash
   ollama create copetra-v1 -f ./Modelfile
   ```
4. Jaribu kuongea nayo:
   ```bash
   ollama run copetra-v1 "Habari yako, wewe ni nani?"
   ```

---

## 4. Kuunganisha na Copetra App ya Railway:

Kwenye `frontend/.env.local` au mazingira ya Railway:
```env
COPETRA_LOCAL_AI_URL=http://<IP_YA_SEVA_YAKO>:11434/v1/chat/completions
COPETRA_LOCAL_AI_MODEL=copetra-v1
```
Mfumo wetu wa gumzo utaanza kutumia modeli hii kama kipaumbele cha kwanza moja kwa moja.
