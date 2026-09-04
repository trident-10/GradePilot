"use client";

import { useRouter } from "next/navigation";
import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useRef,
  useState,
} from "react";

import {
  fetchAcademicSummary,
  fetchCourseImpact,
  fetchFutureSemester,
  fetchManualScenario,
  fetchRequiredSemesterGpa,
  fetchTargetPlan,
  toTurkishCourseImpactMessage,
  toTurkishFutureSemesterMessage,
  toTurkishManualScenarioMessage,
  toTurkishPlannerMessage,
  toTurkishRequiredGpaMessage,
  type AcademicSummary,
  type CourseImpact,
  type FutureSemesterProjection,
  type ManualScenario,
  type ManualScenarioChangeInput,
  type RequiredSemesterGpa,
  type TargetPlan,
} from "@/lib/api/academic";
import {
  analyzeTranscript,
  type AnalyzeApiResponse,
  toTurkishUserMessage,
} from "@/lib/api/transcripts";
import { MAX_TRANSCRIPT_UPLOAD_BYTES } from "@/lib/uploadLimits";
import {
  selectActiveCourses,
  selectHistoricalCourses,
} from "@/lib/courses";
import type {
  AppPhase,
  Course,
  CreditOption,
  TranscriptResult,
} from "@/lib/types";

export type FutureCourseDraft = {
  id: string;
  name: string;
  gpaCredit: string;
  grade: string;
};

function createFutureDraft(): FutureCourseDraft {
  return {
    id:
      typeof crypto !== "undefined" && "randomUUID" in crypto
        ? crypto.randomUUID()
        : `future-${Date.now()}-${Math.random()}`,
    name: "",
    gpaCredit: "",
    grade: "BB",
  };
}

const EMPTY_RESULT: TranscriptResult = {
  formatName: null,
  warnings: [],
  courses: [],
};

function mapCourse(course: AnalyzeApiResponse["courses"][number]): Course {
  return {
    code: course.code,
    name: course.name,
    gpaCredit: course.gpa_credit,
    ects: course.ects,
    localCredit: course.local_credit,
    grade: course.grade,
    semester: course.semester,
    sourceOrder:
      typeof course.source_order === "number" ? course.source_order : null,
  };
}

type AppStateContextValue = {
  phase: AppPhase;
  isReady: boolean;
  isBusy: boolean;
  errorMessage: string | null;
  transcript: TranscriptResult | null;
  creditOptions: CreditOption[];
  pendingCourses: Course[];
  courses: Course[];
  activeCourses: Course[];
  historicalCourses: Course[];
  warnings: string[];
  formatName: string | null;
  weightingMode: string | null;
  academicSummary: AcademicSummary | null;
  summaryLoading: boolean;
  summaryError: string | null;
  plannerResult: TargetPlan | null;
  plannerLoading: boolean;
  plannerError: string | null;
  manualScenarioChanges: ManualScenarioChangeInput[];
  manualScenarioResult: ManualScenario | null;
  manualScenarioLoading: boolean;
  manualScenarioError: string | null;
  uploadFile: (file: File) => Promise<void>;
  selectCreditOption: (optionId: string) => Promise<void>;
  confirmCourses: () => void;
  resetTranscript: () => void;
  clearError: () => void;
  refreshAcademicSummary: () => Promise<void>;
  requestTargetPlan: (input: {
    targetGpa: number;
    maxGrade: string;
    strategy: string;
  }) => Promise<void>;
  clearPlanner: () => void;
  addManualScenarioChange: (change: ManualScenarioChangeInput) => void;
  updateManualScenarioChange: (
    courseCode: string,
    newGrade: string,
  ) => void;
  removeManualScenarioChange: (courseCode: string) => void;
  requestManualScenario: () => Promise<void>;
  clearManualScenario: () => void;
  selectedImpactCourse: string | null;
  courseImpactResult: CourseImpact | null;
  courseImpactLoading: boolean;
  courseImpactError: string | null;
  requestCourseImpact: (courseCode: string) => Promise<void>;
  clearCourseImpact: () => void;
  futureCourses: FutureCourseDraft[];
  futureSemesterResult: FutureSemesterProjection | null;
  futureSemesterLoading: boolean;
  futureSemesterError: string | null;
  addFutureCourse: () => void;
  updateFutureCourse: (
    id: string,
    patch: Partial<Pick<FutureCourseDraft, "name" | "gpaCredit" | "grade">>,
  ) => void;
  removeFutureCourse: (id: string) => void;
  requestFutureSemester: () => Promise<void>;
  clearFutureSemester: () => void;
  requiredGpaResult: RequiredSemesterGpa | null;
  requiredGpaLoading: boolean;
  requiredGpaError: string | null;
  requestRequiredSemesterGpa: (input: {
    targetGpa: number;
    futureGpaWeight: number;
  }) => Promise<void>;
  clearRequiredGpa: () => void;
};

const AppStateContext = createContext<AppStateContextValue | null>(null);

export function AppStateProvider({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const [phase, setPhase] = useState<AppPhase>("empty");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [transcript, setTranscript] = useState<TranscriptResult | null>(null);
  const [creditOptions, setCreditOptions] = useState<CreditOption[]>([]);
  const [pendingCourses, setPendingCourses] = useState<Course[]>([]);
  const [warnings, setWarnings] = useState<string[]>([]);
  const [formatName, setFormatName] = useState<string | null>(null);
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [weightingMode, setWeightingMode] = useState<string | null>(null);
  const [academicSummary, setAcademicSummary] =
    useState<AcademicSummary | null>(null);
  const [summaryLoading, setSummaryLoading] = useState(false);
  const [summaryError, setSummaryError] = useState<string | null>(null);
  const [plannerResult, setPlannerResult] = useState<TargetPlan | null>(null);
  const [plannerLoading, setPlannerLoading] = useState(false);
  const [plannerError, setPlannerError] = useState<string | null>(null);
  const [manualScenarioChanges, setManualScenarioChanges] = useState<
    ManualScenarioChangeInput[]
  >([]);
  const [manualScenarioResult, setManualScenarioResult] =
    useState<ManualScenario | null>(null);
  const [manualScenarioLoading, setManualScenarioLoading] = useState(false);
  const [manualScenarioError, setManualScenarioError] = useState<string | null>(
    null,
  );
  const manualScenarioRequestId = useRef(0);
  const [selectedImpactCourse, setSelectedImpactCourse] = useState<
    string | null
  >(null);
  const [courseImpactResult, setCourseImpactResult] =
    useState<CourseImpact | null>(null);
  const [courseImpactLoading, setCourseImpactLoading] = useState(false);
  const [courseImpactError, setCourseImpactError] = useState<string | null>(
    null,
  );
  const [futureCourses, setFutureCourses] = useState<FutureCourseDraft[]>([
    createFutureDraft(),
  ]);
  const [futureSemesterResult, setFutureSemesterResult] =
    useState<FutureSemesterProjection | null>(null);
  const [futureSemesterLoading, setFutureSemesterLoading] = useState(false);
  const [futureSemesterError, setFutureSemesterError] = useState<string | null>(
    null,
  );
  const [requiredGpaResult, setRequiredGpaResult] =
    useState<RequiredSemesterGpa | null>(null);
  const [requiredGpaLoading, setRequiredGpaLoading] = useState(false);
  const [requiredGpaError, setRequiredGpaError] = useState<string | null>(null);

  const clearPlanner = useCallback(() => {
    setPlannerResult(null);
    setPlannerLoading(false);
    setPlannerError(null);
  }, []);

  const clearManualScenarioResult = useCallback(() => {
    manualScenarioRequestId.current += 1;
    setManualScenarioResult(null);
    setManualScenarioLoading(false);
    setManualScenarioError(null);
  }, []);

  const clearManualScenario = useCallback(() => {
    setManualScenarioChanges([]);
    clearManualScenarioResult();
  }, [clearManualScenarioResult]);

  const clearCourseImpact = useCallback(() => {
    setSelectedImpactCourse(null);
    setCourseImpactResult(null);
    setCourseImpactLoading(false);
    setCourseImpactError(null);
  }, []);

  const clearFutureSemester = useCallback(() => {
    setFutureSemesterResult(null);
    setFutureSemesterLoading(false);
    setFutureSemesterError(null);
  }, []);

  const clearRequiredGpa = useCallback(() => {
    setRequiredGpaResult(null);
    setRequiredGpaLoading(false);
    setRequiredGpaError(null);
  }, []);

  const resetFutureCourses = useCallback(() => {
    setFutureCourses([createFutureDraft()]);
    clearFutureSemester();
  }, [clearFutureSemester]);

  const clearSummary = useCallback(() => {
    setAcademicSummary(null);
    setSummaryLoading(false);
    setSummaryError(null);
    clearPlanner();
    clearManualScenario();
    clearCourseImpact();
    resetFutureCourses();
    clearRequiredGpa();
  }, [
    clearCourseImpact,
    clearManualScenario,
    clearPlanner,
    clearRequiredGpa,
    resetFutureCourses,
  ]);

  const resetTranscript = useCallback(() => {
    setPhase("empty");
    setErrorMessage(null);
    setTranscript(null);
    setCreditOptions([]);
    setPendingCourses([]);
    setWarnings([]);
    setFormatName(null);
    setUploadedFile(null);
    setWeightingMode(null);
    clearSummary();
  }, [clearSummary]);

  const clearError = useCallback(() => {
    setErrorMessage(null);
    setPhase("empty");
    setCreditOptions([]);
    setPendingCourses([]);
    setWarnings([]);
    setFormatName(null);
    setTranscript(null);
    setUploadedFile(null);
    setWeightingMode(null);
    clearSummary();
  }, [clearSummary]);

  const loadAcademicSummary = useCallback(async (courses: Course[]) => {
    setSummaryLoading(true);
    setSummaryError(null);
    setAcademicSummary(null);

    try {
      const summary = await fetchAcademicSummary(courses);
      setAcademicSummary(summary);
    } catch (error) {
      console.error("Academic summary failed", error);
      setSummaryError(toTurkishUserMessage(error));
      setAcademicSummary(null);
    } finally {
      setSummaryLoading(false);
    }
  }, []);

  const enterReady = useCallback(
    async (courses: Course[], nextFormat: string | null, nextWarnings: string[]) => {
      clearManualScenario();
      setCreditOptions([]);
      setPendingCourses([]);
      setTranscript({
        formatName: nextFormat,
        warnings: nextWarnings,
        courses,
      });
      setPhase("ready");
      await loadAcademicSummary(courses);
      router.replace("/genel-bakis");
    },
    [clearManualScenario, loadAcademicSummary, router],
  );

  const applyAnalyzeResponse = useCallback(
    async (response: AnalyzeApiResponse) => {
      setFormatName(response.format);
      setWarnings(response.warnings ?? []);
      setErrorMessage(null);

      if (response.status === "credit_selection") {
        setPhase("credit_selection");
        setCreditOptions(
          (response.credit_options ?? []).map((option) => ({
            id: option.id,
            label: option.label,
          })),
        );
        setPendingCourses([]);
        setTranscript(null);
        clearSummary();
        return;
      }

      const courses = (response.courses ?? []).map(mapCourse);

      if (response.status === "confirmation") {
        setPhase("confirmation");
        setCreditOptions([]);
        setPendingCourses(courses);
        setTranscript({
          ...EMPTY_RESULT,
          formatName: response.format,
          warnings: response.warnings ?? [],
        });
        clearSummary();
        return;
      }

      await enterReady(courses, response.format, response.warnings ?? []);
    },
    [clearSummary, enterReady],
  );

  const uploadFile = useCallback(
    async (file: File) => {
      setPhase("uploading");
      setErrorMessage(null);
      setTranscript(null);
      setCreditOptions([]);
      setPendingCourses([]);
      setWarnings([]);
      setFormatName(null);
      setWeightingMode(null);
      setUploadedFile(file);
      clearSummary();

      const looksLikePdf =
        file.type === "application/pdf" ||
        file.name.toLowerCase().endsWith(".pdf");
      if (!looksLikePdf) {
        setErrorMessage("Yüklenen dosya geçerli bir PDF değil.");
        setPhase("error");
        return;
      }
      if (file.size > MAX_TRANSCRIPT_UPLOAD_BYTES) {
        setErrorMessage(
          "PDF dosyası çok büyük. Maksimum 10 MB yükleyebilirsin.",
        );
        setPhase("error");
        return;
      }

      try {
        const response = await analyzeTranscript(file);
        await applyAnalyzeResponse(response);
      } catch (error) {
        console.error("Transcript analyze failed", error);
        setErrorMessage(toTurkishUserMessage(error));
        setPhase("error");
      }
    },
    [applyAnalyzeResponse, clearSummary],
  );

  const selectCreditOption = useCallback(
    async (optionId: string) => {
      if (!uploadedFile) {
        setErrorMessage(
          "Yüklenen PDF bulunamadı. Lütfen transkripti yeniden yükle.",
        );
        setPhase("error");
        return;
      }

      setPhase("uploading");
      setErrorMessage(null);
      setWeightingMode(optionId);
      clearSummary();

      try {
        const response = await analyzeTranscript(uploadedFile, optionId);
        await applyAnalyzeResponse(response);
      } catch (error) {
        console.error("Weighting selection failed", error);
        setErrorMessage(toTurkishUserMessage(error));
        setPhase("error");
      }
    },
    [applyAnalyzeResponse, clearSummary, uploadedFile],
  );

  const confirmCourses = useCallback(() => {
    if (pendingCourses.length === 0) {
      setErrorMessage("Onaylanacak ders verisi yok.");
      setPhase("error");
      return;
    }

    void enterReady(pendingCourses, formatName, warnings);
  }, [enterReady, formatName, pendingCourses, warnings]);

  const refreshAcademicSummary = useCallback(async () => {
    const courses = transcript?.courses ?? [];
    if (courses.length === 0) {
      return;
    }
    await loadAcademicSummary(courses);
  }, [loadAcademicSummary, transcript?.courses]);

  const requestTargetPlan = useCallback(
    async (input: {
      targetGpa: number;
      maxGrade: string;
      strategy: string;
    }) => {
      const courses = transcript?.courses ?? [];
      if (courses.length === 0) {
        setPlannerError("Hesaplanacak ders bulunamadı. Transkripti yeniden yükle.");
        setPlannerResult(null);
        return;
      }

      setPlannerLoading(true);
      setPlannerError(null);
      setPlannerResult(null);

      try {
        const plan = await fetchTargetPlan(courses, input);
        setPlannerResult(plan);
      } catch (error) {
        console.error("Target plan failed", error);
        setPlannerError(toTurkishPlannerMessage(error));
        setPlannerResult(null);
      } finally {
        setPlannerLoading(false);
      }
    },
    [transcript?.courses],
  );

  const addManualScenarioChange = useCallback(
    (change: ManualScenarioChangeInput) => {
      setManualScenarioChanges((current) => {
        if (current.some((row) => row.courseCode === change.courseCode)) {
          return current;
        }
        return [...current, change];
      });
      clearManualScenarioResult();
    },
    [clearManualScenarioResult],
  );

  const removeManualScenarioChange = useCallback(
    (courseCode: string) => {
      setManualScenarioChanges((current) =>
        current.filter((row) => row.courseCode !== courseCode),
      );
      clearManualScenarioResult();
    },
    [clearManualScenarioResult],
  );

  const updateManualScenarioChange = useCallback(
    (courseCode: string, newGrade: string) => {
      setManualScenarioChanges((current) =>
        current.map((row) =>
          row.courseCode === courseCode ? { ...row, newGrade } : row,
        ),
      );
      clearManualScenarioResult();
    },
    [clearManualScenarioResult],
  );

  const requestManualScenario = useCallback(async () => {
    const courses = transcript?.courses ?? [];
    if (courses.length === 0) {
      setManualScenarioError(
        "Hesaplanacak ders bulunamadı. Transkripti yeniden yükle.",
      );
      setManualScenarioResult(null);
      return;
    }
    if (manualScenarioChanges.length === 0) {
      setManualScenarioError("Planına en az bir ders eklemelisin.");
      setManualScenarioResult(null);
      return;
    }

    setManualScenarioLoading(true);
    setManualScenarioError(null);
    setManualScenarioResult(null);
    const requestId = manualScenarioRequestId.current + 1;
    manualScenarioRequestId.current = requestId;
    try {
      const result = await fetchManualScenario(
        courses,
        manualScenarioChanges,
      );
      if (manualScenarioRequestId.current === requestId) {
        setManualScenarioResult(result);
      }
    } catch (error) {
      if (manualScenarioRequestId.current !== requestId) return;
      console.error("Manual scenario failed", error);
      setManualScenarioError(toTurkishManualScenarioMessage(error));
      setManualScenarioResult(null);
    } finally {
      if (manualScenarioRequestId.current === requestId) {
        setManualScenarioLoading(false);
      }
    }
  }, [manualScenarioChanges, transcript?.courses]);

  const requestCourseImpact = useCallback(
    async (courseCode: string) => {
      const courses = transcript?.courses ?? [];
      setSelectedImpactCourse(courseCode);
      setCourseImpactResult(null);
      setCourseImpactError(null);

      if (courses.length === 0) {
        setCourseImpactError(
          "Hesaplanacak ders bulunamadı. Transkripti yeniden yükle.",
        );
        return;
      }

      setCourseImpactLoading(true);
      try {
        const impact = await fetchCourseImpact(courses, courseCode);
        setCourseImpactResult(impact);
      } catch (error) {
        console.error("Course impact failed", error);
        setCourseImpactError(toTurkishCourseImpactMessage(error));
        setCourseImpactResult(null);
      } finally {
        setCourseImpactLoading(false);
      }
    },
    [transcript?.courses],
  );

  const addFutureCourse = useCallback(() => {
    setFutureCourses((current) => [...current, createFutureDraft()]);
    clearFutureSemester();
  }, [clearFutureSemester]);

  const updateFutureCourse = useCallback(
    (
      id: string,
      patch: Partial<Pick<FutureCourseDraft, "name" | "gpaCredit" | "grade">>,
    ) => {
      setFutureCourses((current) =>
        current.map((row) => (row.id === id ? { ...row, ...patch } : row)),
      );
      clearFutureSemester();
    },
    [clearFutureSemester],
  );

  const removeFutureCourse = useCallback(
    (id: string) => {
      setFutureCourses((current) => {
        const next = current.filter((row) => row.id !== id);
        return next.length > 0 ? next : [createFutureDraft()];
      });
      clearFutureSemester();
    },
    [clearFutureSemester],
  );

  const requestFutureSemester = useCallback(async () => {
    const courses = transcript?.courses ?? [];
    if (courses.length === 0) {
      setFutureSemesterError(
        "Hesaplanacak ders bulunamadı. Transkripti yeniden yükle.",
      );
      setFutureSemesterResult(null);
      return;
    }

    const validRows = futureCourses.filter(
      (row) => row.name.trim() !== "" && row.gpaCredit.trim() !== "",
    );
    if (validRows.length === 0) {
      setFutureSemesterError("En az bir gelecek dönem dersi eklemelisin.");
      setFutureSemesterResult(null);
      return;
    }

    setFutureSemesterLoading(true);
    setFutureSemesterError(null);
    setFutureSemesterResult(null);

    try {
      const projection = await fetchFutureSemester(
        courses,
        validRows.map((row) => ({
          name: row.name.trim(),
          gpaCredit: Number(row.gpaCredit.replace(",", ".")),
          grade: row.grade,
        })),
      );
      setFutureSemesterResult(projection);
    } catch (error) {
      console.error("Future semester failed", error);
      setFutureSemesterError(toTurkishFutureSemesterMessage(error));
      setFutureSemesterResult(null);
    } finally {
      setFutureSemesterLoading(false);
    }
  }, [futureCourses, transcript?.courses]);

  const requestRequiredSemesterGpa = useCallback(
    async (input: { targetGpa: number; futureGpaWeight: number }) => {
      const courses = transcript?.courses ?? [];
      if (courses.length === 0) {
        setRequiredGpaError(
          "Hesaplanacak ders bulunamadı. Transkripti yeniden yükle.",
        );
        setRequiredGpaResult(null);
        return;
      }

      setRequiredGpaLoading(true);
      setRequiredGpaError(null);
      setRequiredGpaResult(null);

      try {
        const result = await fetchRequiredSemesterGpa(courses, input);
        setRequiredGpaResult(result);
      } catch (error) {
        console.error("Required semester GPA failed", error);
        setRequiredGpaError(toTurkishRequiredGpaMessage(error));
        setRequiredGpaResult(null);
      } finally {
        setRequiredGpaLoading(false);
      }
    },
    [transcript?.courses],
  );

  const value = useMemo<AppStateContextValue>(() => {
    const result = transcript;
    return {
      phase,
      isReady: phase === "ready",
      isBusy: phase === "uploading",
      errorMessage,
      transcript,
      creditOptions,
      pendingCourses,
      courses: result?.courses ?? [],
      activeCourses: selectActiveCourses(result?.courses ?? []),
      historicalCourses: selectHistoricalCourses(result?.courses ?? []),
      warnings,
      formatName,
      weightingMode,
      academicSummary,
      summaryLoading,
      summaryError,
      plannerResult,
      plannerLoading,
      plannerError,
      manualScenarioChanges,
      manualScenarioResult,
      manualScenarioLoading,
      manualScenarioError,
      uploadFile,
      selectCreditOption,
      confirmCourses,
      resetTranscript,
      clearError,
      refreshAcademicSummary,
      requestTargetPlan,
      clearPlanner,
      addManualScenarioChange,
      updateManualScenarioChange,
      removeManualScenarioChange,
      requestManualScenario,
      clearManualScenario,
      selectedImpactCourse,
      courseImpactResult,
      courseImpactLoading,
      courseImpactError,
      requestCourseImpact,
      clearCourseImpact,
      futureCourses,
      futureSemesterResult,
      futureSemesterLoading,
      futureSemesterError,
      addFutureCourse,
      updateFutureCourse,
      removeFutureCourse,
      requestFutureSemester,
      clearFutureSemester,
      requiredGpaResult,
      requiredGpaLoading,
      requiredGpaError,
      requestRequiredSemesterGpa,
      clearRequiredGpa,
    };
  }, [
    academicSummary,
    addManualScenarioChange,
    addFutureCourse,
    clearCourseImpact,
    clearError,
    clearFutureSemester,
    clearManualScenario,
    clearPlanner,
    clearRequiredGpa,
    confirmCourses,
    courseImpactError,
    courseImpactLoading,
    courseImpactResult,
    creditOptions,
    errorMessage,
    formatName,
    futureCourses,
    futureSemesterError,
    futureSemesterLoading,
    futureSemesterResult,
    manualScenarioChanges,
    manualScenarioError,
    manualScenarioLoading,
    manualScenarioResult,
    pendingCourses,
    phase,
    plannerError,
    plannerLoading,
    plannerResult,
    refreshAcademicSummary,
    removeFutureCourse,
    removeManualScenarioChange,
    requestCourseImpact,
    requestFutureSemester,
    requestManualScenario,
    requestRequiredSemesterGpa,
    requestTargetPlan,
    requiredGpaError,
    requiredGpaLoading,
    requiredGpaResult,
    resetTranscript,
    selectCreditOption,
    selectedImpactCourse,
    summaryError,
    summaryLoading,
    transcript,
    updateManualScenarioChange,
    updateFutureCourse,
    uploadFile,
    warnings,
    weightingMode,
  ]);

  return (
    <AppStateContext.Provider value={value}>{children}</AppStateContext.Provider>
  );
}

export function useAppState() {
  const context = useContext(AppStateContext);
  if (!context) {
    throw new Error("useAppState, AppStateProvider içinde kullanılmalıdır.");
  }
  return context;
}
