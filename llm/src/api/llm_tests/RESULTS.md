# Results of Model Testing

| Test # | Main RAG        | LightRAG         | Auxiliary Agents | Accuracy                                        | Test Duration |
| ------ | --------------- | ---------------- | ---------------- | ----------------------------------------------- | ------------- |
| 1      | gpt-4.1-mini    | gpt-4.1-mini     | gpt-4.1-nano     | 55 – 60 %                                       | 8 minutes     |
| 2      | gpt-4.5-preview | gpt-4.5-preview  | gpt-4.1-mini    | 45 %                                            | 15 minutes    |
| 3      | o4-mini         | gpt-4.1-mini    | gpt-4.1-mini     | 50 – 55 %                                       | 17 minutes    |
| 4      | gpt-4.1         | gpt-4.1-mini     | gpt-4.1          | 55 – 75 % *(currently 55 %, expected to improve with more data)* | 6 minutes     |
