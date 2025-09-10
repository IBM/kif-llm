import React, { useState } from 'react';
import { useForm, Controller } from 'react-hook-form';
import { api } from '@services/api';
import { useQuery } from '@tanstack/react-query';
import {
    Box, Button, CircularProgress, Fab, MenuItem, Select, TextField,
    Typography, InputLabel, FormControl, OutlinedInput, Chip,
    FormHelperText, IconButton, Menu, Switch, ListItemText, Snackbar, Alert
} from '@mui/material';

import { MoreVert } from '@mui/icons-material';
import SettingsIcon from '@mui/icons-material/Settings';
import { StatementsTable } from '@components/StatmentsTable/StatmentsTable'
import { plainToInstance } from 'class-transformer';
import { validateOrReject, ValidationError } from 'class-validator';
import logo from '@assets/kif-qa.svg';
import { DebugModal } from './DebugModal';
import { ConfigDrawer } from './ConfigDrawer';

import { Filter, LinkedEntity, QueryResponse, Statement, Triple } from '../../model/Wikidata';

export type FilterValues = {
   filters: Filter[]
   stores: string[];
   annotated: boolean;
}

type FormValues = {
    query: string;
    stores: string[];
    annotated: boolean;
    provider?: string;
    model?: string;
    apiKey?: string;
    endpoint?: string;
};

const providerModels: Record<string, Record<string, string>> = {
    IBM: {
        'LLama4-Maverick': 'meta-llama/llama-4-maverick-17b-128e-instruct-fp8',
        'LLama3-70B': 'meta-llama/llama-3-3-70b-instruct',
        'Mistral-Medium': 'mistralai/mistral-medium-2505'
    },
    OpenAI: {'GPT4o': 'GPT4o'},
    Ollama: {'LLama2': 'LLama2'}
};

export const Home: React.FC = () => {
    const [queryResponse, setQueryResponse] = useState<QueryResponse>();
    const [statements, setStatements] = useState<Statement[]>([]);
    const [showDebug, setShowDebug] = useState(false);
    const [loading, setLoading] = useState(false);
    const [annotated, setAnnotated] = useState(false);
    const [query, setQuery] = useState('');
    const [storesSelected, setStoresSelected] = useState<string[]>([]);

    const [menuAnchor, setMenuAnchor] = useState<null | HTMLElement>(null);
    const [debugOpen, setDebugOpen] = useState(false);
    const [alertOpen, setAlertOpen] = useState(false);
    const [errorMessage, setErrorMessage] = useState<string | null>(null);

    const [configModel, setConfigModel] = useState<boolean>(false);
    const [configOpen, setConfigOpen] = useState(false);

    const [serverStatus, setServerStatus] = useState<boolean>(false)

    React.useEffect(() => {
        checkStatus();
    }, []);

    const checkStatus = async () => {
        const res = await api.get('/status').then((resp) => {
            return resp.data as { "status": number }
        });

        if (res.status === 200) {
            setServerStatus(true)
        }
    }

    React.useEffect(() => {
        checkModel();
    }, []);

    const checkModel = async () => {
        const res = await api.get('/model').then((resp) => {
            return resp.data as { "model": boolean }
        });

        setConfigModel(res.model);
    }

    const handleConfigMenu = (event: React.MouseEvent<HTMLElement>) => {
        if (configOpen) {
            setConfigOpen(false)
        }
        else {
            setConfigOpen(true)
        }
    };

    const handleMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
        setMenuAnchor(event.currentTarget);
    };

    const handleMenuClose = () => {
        setMenuAnchor(null);
    };

    const handleCloseAlert = (_event?: React.SyntheticEvent, reason?: string) => {
        if (reason === 'clickaway') return;
        setAlertOpen(false);
    };

    const { control, handleSubmit, watch } = useForm<FormValues>({
        defaultValues: { query: '', stores: [], annotated: false },
    });

    const { data: stores, isLoading } = useQuery({
        queryKey: ['stores'],
        queryFn: async () => {
            const res = await api.get('/stores');
            return res.data as { id: string; description: string }[];
        },
    });

    const [triples, setTriples] = useState<Triple[]>();
    const [filters, setFilters] = useState<Filter[]>();
    const [linkedEntities, setLinkedEntities] = useState<LinkedEntity[]>();
    const [linkedProperties, setLinkedProperties] = useState<LinkedEntity[]>();


    const onFilter = async (data: FilterValues) => {
        setLoading(true);
        setStatements([])
        setDebugOpen(false)
        let res = null
        try {
            res = await api.post('/filter', data);
        }
        catch (error: any){
            const error_data = error?.response?.data?.error
            if (error_data){
                setErrorMessage(error_data);
            }
            else {
                setErrorMessage(error.message);
            }

            setAlertOpen(true);
        }
        try {
            if (res) {
                const stmts: Statement[] = plainToInstance(Statement, res.data as object[]);
                if (stmts) {
                    await Promise.all(stmts.map(stmt => validateOrReject(stmt)));
                    setStatements(stmts);
                    setShowDebug(true)
                }
                else {
                    setStatements([]);
                }
            }
            else {
                setStatements([]);
            }
        }
        catch {
            setErrorMessage('An error occurred while validating the statements format.');
            setAlertOpen(true)
            setStatements([]);
        }
        setLoading(false);
    };

    const onAsk = async (data: FormValues) => {
        setLoading(true);
        setStatements([])
        setShowDebug(false)
        try {
            setQuery(data.query)
            setStoresSelected(data.stores)
            setAnnotated(data.annotated)
            const res = await api.post('/query', data);
            const response: QueryResponse = plainToInstance(QueryResponse, res.data as object);
            if (response) {
                if (response.statements) {
                    await Promise.all(response.statements.map(stmt => validateOrReject(stmt)));
                    setStatements(response.statements);
                    if (response.pattern) {
                        const triples = []
                        for (const t of response.pattern) {
                            triples.push({
                                'subject': t.subject,
                                'predicate': t.predicate,
                                'object': t.object
                            })
                        }
                        setTriples(triples)
                        setLinkedEntities(response.items)
                        setLinkedProperties(response.properties)
                        setFilters(response.filters)
                    }
                }
                setShowDebug(true)
            }
        } catch (error: any) {
            const error_data = error?.response?.data?.error
            if (error_data !== null){
                setErrorMessage(error_data);
            }
            else {
                setErrorMessage(error.message);
            }
            setAlertOpen(true);
            setStatements([]);
        }

        setLoading(false);
    };

    const onDebug = async () => {
        setDebugOpen(true);
    };

    return (
        <Box
            display="flex"
            flexDirection="column"
            minHeight="100vh"
        >
            {!serverStatus && (<Alert severity='error'>
                    Can not connect to the server, please contact the owner of the project.
                </Alert>)}
            {serverStatus && !configModel && (<Alert severity='warning'>
                    You need to configure your LLM settings before asking questions.
                </Alert>)}
        <Snackbar
                open={ alertOpen }
                autoHideDuration={5000} // 5 segundos
                sx={{marginTop: 0}}
                anchorOrigin={{ vertical: 'top', horizontal: 'center' }}>
                <Alert onClose={handleCloseAlert} severity="error" sx={{ width: '100%' }}>
                {errorMessage}
                </Alert>
            </Snackbar>
            <Box
                display="flex"
                flexDirection="column"
                alignItems="center"
                justifyContent="flex-start"
                gap={3}
                sx={{ py: 2 }}    // optional padding
            >
                <ConfigDrawer
                    open={configOpen}
                    onClose={() => setConfigOpen(false)}
                    checkModel={checkModel}
                    providerModels={providerModels}
                />

                <img src={logo} alt="KIF QA" style={{ width: 200, height: 'auto' }} />
                <Typography variant="h4">Ask a Simple Question</Typography>

                <Controller
                    name="query"
                    control={control}
                    rules={{ required: 'Question is required' }}
                    render={({ field, fieldState }) => (
                        <TextField
                            {...field}
                            label="Question"
                            variant="outlined"
                            fullWidth
                            sx={{ maxWidth: 500 }}
                            error={!!fieldState.error}
                            helperText={fieldState.error?.message}
                            InputProps={{
                                endAdornment: (
                                    <IconButton onClick={handleMenuOpen} size="small">
                                        <MoreVert />
                                    </IconButton>
                                )
                            }}
                            disabled={!configModel || !serverStatus}
                        />
                    )}
                />
                {configModel && (
                    <Menu
                        anchorEl={menuAnchor}
                        open={Boolean(menuAnchor)}
                        onClose={handleMenuClose}>
                        <MenuItem disableRipple sx={{ display: 'flex', justifyContent: 'space-between' }} disabled={!configModel || !serverStatus}>
                            <ListItemText primary="Annotated" />

                            <Controller
                                name="annotated"
                                control={control}
                                render={({ field }) => (
                                    <Switch
                                        edge="end"
                                        checked={field.value}
                                        onChange={(e) => field.onChange(e.target.checked)}
                                    />
                                )}
                            />
                        </MenuItem>
                    </Menu>
                )}

                {isLoading && serverStatus ? (
                    <CircularProgress />
                ) : (
                    <Controller
                        name="stores"
                        control={control}
                        rules={{ required: 'Select at least one source' }}
                        render={({ field, fieldState }) => (
                            <FormControl sx={{ maxWidth: 500, width: '100%' }} error={!!fieldState.error}>
                                <InputLabel sx={{color: configModel ? '#00000099' : '#00000061'}}>Sources</InputLabel>
                                <Select
                                    {...field}
                                    disabled={!configModel || !serverStatus}
                                    multiple
                                    input={<OutlinedInput label="Sources" />}
                                    renderValue={(selected) => (
                                        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                                            {selected.map((value) => {
                                                const kb = stores?.find((kb) => kb.id === value);
                                                return <Chip key={value} label={kb?.id || value} sx={{ fontSize: 16 }} />;
                                            })}
                                        </Box>
                                    )}
                                >
                                    {stores?.map((kb) => (
                                        <MenuItem key={kb.id} value={kb.id}>
                                            {kb.id}: {kb.description}
                                        </MenuItem>
                                    ))}
                                </Select>
                                {fieldState.error && <FormHelperText>{fieldState.error.message}</FormHelperText>}
                            </FormControl>
                        )}
                    />
                )}

                <Box display="flex" gap={2}>
                    <Button variant="contained" color="primary" onClick={handleSubmit(onAsk)} disabled={loading || !configModel || !serverStatus}>
                        {loading ? <CircularProgress size={24} /> : 'Ask'}
                    </Button>
                    {showDebug && (
                        <Button variant="outlined" color="secondary" onClick={handleSubmit(onDebug)}>
                            Details
                        </Button>
                    )}
                </Box>

                {statements.length > 0 && (
                    <Box sx={{ width: '100%', maxWidth: { xs: '100%', sm: '90%', md: '80%' } }}>
                        <StatementsTable statements={statements} />
                    </Box>
                )}

                {triples && (
                    <DebugModal
                        debugOpen={debugOpen}
                        filters={filters}
                        triples={triples}
                        linkedEntities={linkedEntities}
                        linkedProperties={linkedProperties}
                        onClose={() => setDebugOpen(false)}
                        onRun={onFilter}
                        query={query}
                        annotated={annotated}
                        stores={storesSelected}
                        onUpdateFilters={setFilters}
                        onUpdateEntities={setLinkedEntities}
                        onUpdateProperties={setLinkedProperties} />
                )}
                {/* Floating Action Button for Debug */}
                <Fab
                    color="primary"
                    aria-label="settings"
                    onClick={handleConfigMenu}
                    sx={{
                        position: 'fixed',
                        bottom: 16,
                        right: 16,
                        zIndex: 1300
                    }}
                    disabled={!serverStatus}>
                    <SettingsIcon />
                </Fab>
            </Box>
            {/* Footer */}
            <Typography
                variant="caption"
                color="text.secondary"
                sx={{
                    textAlign: 'center',
                    backgroundColor: 'background.paper',
                    width: '100%',
                    py: 1,
                    position: 'fixed',
                    bottom: 0,
                    left: 0,
                    right: 0,
                    boxShadow: '0 -2px 5px rgba(0,0,0,0.1)',
                    zIndex: 1200,
                }}
            >
                KIF-QA can make mistakes. Please, check important information.
                <br />
                © 2025 IBM Corp.
            </Typography>
        </Box>
    );
};
