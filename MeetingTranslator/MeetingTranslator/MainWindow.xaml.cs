using System;
using System.Text.Json;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;
using System.Net.WebSockets;
using System.Text;
using System.Threading;
using System.Threading.Tasks;

namespace MeetingTranslator
{
    public partial class MainWindow : Window
    {
        public MainWindow()
        {
            InitializeComponent();
            this.Loaded += (s, e) => ConectarAlCerebro();
        }

        private void ArrastrarVentana(object sender, MouseButtonEventArgs e)
        {
            if (e.ChangedButton == MouseButton.Left) this.DragMove();
        }

        // --- LA MAGIA DEL HISTORIAL ---
        private void AgregarSubtituloAlHistorial(string textoSuperior, string textoInferior)
        {
            // 1. Limpiamos el mensaje inicial si es la primera vez que recibimos algo
            if (PanelHistorial.Children.Count > 0 && PanelHistorial.Children[0] is TextBlock primerTb &&
               (primerTb.Text.Contains("Buscando") || primerTb.Text.Contains("Iniciando")))
            {
                PanelHistorial.Children.Clear();
            }

            // 2. Creamos el texto de arriba (Inglés o Traducción al Inglés)
            var txtSup = new TextBlock
            {
                Text = textoSuperior,
                Foreground = System.Windows.Media.Brushes.LightGray,
                FontSize = 18,
                TextWrapping = TextWrapping.Wrap // Permite que el texto baje de línea si es muy largo
            };

            // 3. Creamos el texto de abajo (Español o Traducción al Español)
            var txtInf = new TextBlock
            {
                Text = textoInferior,
                Foreground = System.Windows.Media.Brushes.White,
                FontSize = 24,
                FontWeight = FontWeights.Bold,
                Margin = new Thickness(0, 2, 0, 20), // Separación grande entre cada bloque de traducción
                TextWrapping = TextWrapping.Wrap
            };

            // 4. Los agregamos a la pantalla
            PanelHistorial.Children.Add(txtSup);
            PanelHistorial.Children.Add(txtInf);

            // 5. REGLA DE LIMPIEZA: Mantenemos solo los últimos 15 pares de mensajes (30 TextBlocks en total).
            // Esto asegura que la app sea ultraligera y nunca consuma RAM extra, sin importar si la junta dura 5 horas.
            while (PanelHistorial.Children.Count > 30)
            {
                PanelHistorial.Children.RemoveAt(0);
            }

            // 6. Auto-Scroll: Empujamos la vista hasta el fondo para leer siempre lo más reciente
            ScrollSubtitulos.ScrollToBottom();
        }

        private async void ConectarAlCerebro()
        {
            try
            {
                using (var ws = new ClientWebSocket())
                {
                    var uri = new Uri("ws://127.0.0.1:8765");
                    await ws.ConnectAsync(uri, CancellationToken.None);

                    var buffer = new byte[8192];
                    while (ws.State == WebSocketState.Open)
                    {
                        var result = await ws.ReceiveAsync(new ArraySegment<byte>(buffer), CancellationToken.None);
                        if (result.MessageType == WebSocketMessageType.Text)
                        {
                            var mensajeJsonCrudo = Encoding.UTF8.GetString(buffer, 0, result.Count);

                            Dispatcher.Invoke(() =>
                            {
                                try
                                {
                                    var opciones = new JsonSerializerOptions { PropertyNameCaseInsensitive = true };
                                    var traduccion = JsonSerializer.Deserialize<MensajeTraduccion>(mensajeJsonCrudo, opciones);

                                    // Usamos nuestra nueva función en lugar de sobrescribir
                                    AgregarSubtituloAlHistorial(
                                        traduccion?.original ?? "",
                                        traduccion?.traduccion ?? ""
                                    );
                                }
                                catch
                                {
                                    AgregarSubtituloAlHistorial("Error de Formato JSON:", mensajeJsonCrudo);
                                }
                            });
                        }
                    }
                }
            }
            catch
            {
                Dispatcher.Invoke(() =>
                {
                    // Si se desconecta, borramos todo y ponemos el aviso
                    PanelHistorial.Children.Clear();
                    AgregarSubtituloAlHistorial("Buscando conexión...", "Esperando al script de Python...");
                });

                await Task.Delay(2000);
                ConectarAlCerebro();
            }
        }
    }

    public class MensajeTraduccion
    {
        public string? original { get; set; }
        public string? traduccion { get; set; }
    }
}